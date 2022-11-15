#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
from servicecatalog_puppet import serialisation_utils, remote_config
import logging
import os
import shutil
import sys
import time
import urllib
from glob import glob
from pathlib import Path
from urllib.request import urlretrieve

import click
import colorclass
import luigi
import terminaltables
import yaml
from betterboto import client as betterboto_client
from colorclass import Color
from luigi import LuigiStatusCode

from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet import environmental_variables
from servicecatalog_puppet.waluigi import scheduler_factory
from servicecatalog_puppet.workflow import tasks

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def get_build_status_for_in(build_id, spoke_account_id):
    with betterboto_client.CrossAccountClientContextManager(
        "codebuild",
        config.get_puppet_role_arn(spoke_account_id),
        f"{spoke_account_id}-{config.get_puppet_role_name()}",
    ) as codebuild_client:
        response = codebuild_client.batch_get_builds(ids=[build_id])
        build = response.get("builds")[0]
        status = build.get("buildStatus")
        has_failed = status not in ["IN_PROGRESS", "SUCCEEDED"]
        is_running = status == "IN_PROGRESS"
        logger.info(
            f"Checking for status of {build_id} in {spoke_account_id}. status: {status}, has failed: {has_failed}, is running: {is_running}"
        )
        return status, build, has_failed, is_running


def run_tasks(
    puppet_account_id,
    current_account_id,
    tasks_to_run,
    num_workers,
    is_dry_run=False,
    is_list_launches=None,
    execution_mode="hub",
    on_complete_url=None,
    running_exploded=False,
    tasks_to_run_filtered=[],
    manifest_files_path="",
    manifest_task_reference_file_path="",
):
    codebuild_id = os.getenv("CODEBUILD_BUILD_ID", "LOCAL_BUILD")
    if is_list_launches:
        should_use_eventbridge = False
        should_forward_failures_to_opscenter = False
    else:
        should_use_eventbridge = config.get_should_use_eventbridge() and not is_dry_run
        should_forward_failures_to_opscenter = (
            config.get_should_forward_failures_to_opscenter() and not is_dry_run
        )

    ssm_client = None
    if should_forward_failures_to_opscenter:
        with betterboto_client.ClientContextManager("ssm") as ssm:
            ssm_client = ssm

    entries = []

    for result_type in [
        "start",
        "failure",
        "success",
        "timeout",
        "process_failure",
        "processing_time",
        "broken_task",
        "traces",
    ]:
        if not os.path.exists(Path(constants.RESULTS_DIRECTORY) / result_type):
            os.makedirs(Path(constants.RESULTS_DIRECTORY) / result_type)

    if not os.path.exists(Path(constants.OUTPUT)):
        os.makedirs(Path(constants.OUTPUT))

    logger.info(f"About to run workflow with {num_workers} workers")

    if not (running_exploded or is_list_launches):
        tasks.print_stats()

    output_cache_starting_point = config.get_output_cache_starting_point()
    logger.info("CHECKING output_cache_starting_point")
    if output_cache_starting_point != "":
        logger.info("UNZIPPING output_cache_starting_point")
        dst = "GetSSMParamTask.zip"
        urlretrieve(output_cache_starting_point, dst)
        shutil.unpack_archive("GetSSMParamTask.zip", ".", "zip")

    threads_or_processes = config.get_scheduler_threads_or_processes()
    scheduler = scheduler_factory.get_scheduler(
        threads_or_processes, "topological_generations"
    )
    scheduler.run(
        num_workers,
        tasks_to_run_filtered,
        manifest_files_path,
        manifest_task_reference_file_path,
        puppet_account_id,
        execution_mode,
    )

    cache_invalidator = os.environ.get(environmental_variables.CACHE_INVALIDATOR)

    has_failures = len(glob("results/failure/*", recursive=True))
    has_spoke_failures = False

    if execution_mode == constants.EXECUTION_MODE_HUB:
        logger.info("Checking spoke executions...")
        all_run_deploy_in_spoke_tasks = glob(
            f"output/RunDeployInSpokeTask/**/{cache_invalidator}.json", recursive=True,
        )
        n_all_run_deploy_in_spoke_tasks = len(all_run_deploy_in_spoke_tasks)
        index = 0
        for filename in all_run_deploy_in_spoke_tasks:
            result = serialisation_utils.json_loads(open(filename, "r").read())
            spoke_account_id = result.get("account_id")
            build = result.get("build")
            build_id = build.get("id")
            logger.info(
                f"[{index}/{n_all_run_deploy_in_spoke_tasks}] Checking spoke execution for account: {spoke_account_id} build: {build_id}"
            )
            index += 1

            status = "IN_PROGRESS"

            while status == "IN_PROGRESS":
                status, build, has_failed, is_running = get_build_status_for_in(
                    build_id, spoke_account_id
                )
                if has_failed:
                    has_spoke_failures = True
                    params_for_results = dict(
                        account_id=spoke_account_id, build_id=build_id
                    )
                    for ev in build.get("environment").get("environmentVariables", []):
                        params_for_results[ev.get("name")] = ev.get("value")
                    failure = dict(
                        event_type="failure",
                        task_type="RunDeployInSpokeTask",
                        task_params=params_for_results,
                        params_for_results=params_for_results,
                        exception_type="<class 'Exception'>",
                        exception_stack_trace=[
                            f"Codebuild in spoke did not succeed: {build.get('buildStatus')}"
                        ],
                    )
                    open(
                        f"results/failure/RunDeployInSpokeTask-{spoke_account_id}.json",
                        "w",
                    ).write(json.dumps(failure))
                elif is_running:
                    time.sleep(10)

    dry_run_tasks = (
        glob(
            f"output/ProvisionProductDryRunTask/**/{cache_invalidator}.json",
            recursive=True,
        )
        + glob(
            f"output/TerminateProductDryRunTask/**/{cache_invalidator}.json",
            recursive=True,
        )
        + glob(
            f"output/ProvisionStackDryRunTask/**/{cache_invalidator}.json",
            recursive=True,
        )
        + glob(
            f"output/TerminateStackDryRunTask/**/{cache_invalidator}.json",
            recursive=True,
        )
    )

    if is_list_launches:
        if is_list_launches == "table":
            table = [
                [
                    "account_id",
                    "region",
                    "launch/stack",
                    "portfolio",
                    "product",
                    "expected_version",
                    "actual_version",
                    "active",
                    "status",
                ]
            ]

            for filename in dry_run_tasks:
                result = serialisation_utils.json_loads(open(filename, "r").read())
                current_version = (
                    Color("{green}" + result.get("current_version") + "{/green}")
                    if result.get("current_version") == result.get("new_version")
                    else Color("{red}" + result.get("current_version") + "{/red}")
                )

                active = (
                    Color("{green}" + str(result.get("active")) + "{/green}")
                    if result.get("active")
                    else Color("{red}" + str(result.get("active")) + "{/red}")
                )

                current_status = (
                    Color("{green}" + result.get("current_status") + "{/green}")
                    if result.get("current_status") == "AVAILABLE"
                    else Color("{red}" + result.get("current_status") + "{/red}")
                )

                table.append(
                    [
                        result.get("params").get("account_id"),
                        result.get("params").get("region"),
                        f'Launch:{result.get("params").get("launch_name")}'
                        if result.get("params").get("launch_name")
                        else f'Stack:{result.get("params").get("stack_name")}',
                        result.get("params").get("portfolio"),
                        result.get("params").get("product"),
                        result.get("new_version"),
                        current_version,
                        active,
                        current_status,
                    ]
                )
            click.echo(terminaltables.AsciiTable(table).table)

        elif is_list_launches == "json":
            results = dict()
            for filename in glob(
                f"output/ProvisionProductDryRunTask/**/{cache_invalidator}.json",
                recursive=True,
            ):
                result = serialisation_utils.json_loads(open(filename, "r").read())
                account_id = result.get("params").get("account_id")
                region = result.get("params").get("region")
                launch_name = result.get("params").get("launch_name")
                results[f"{account_id}_{region}_{launch_name}"] = dict(
                    account_id=account_id,
                    region=region,
                    launch=launch_name,
                    portfolio=result.get("params").get("portfolio"),
                    product=result.get("params").get("product"),
                    expected_version=result.get("new_version"),
                    actual_version=result.get("current_version"),
                    active=result.get("active"),
                    status=result.get("current_status"),
                )

            click.echo(json.dumps(results, indent=4, default=str,))

        else:
            raise Exception(f"Unsupported format: {is_list_launches}")

    else:
        click.echo("Results")
        if is_dry_run:
            table_data = [
                [
                    "Result",
                    "Launch/Stack",
                    "Account",
                    "Region",
                    "Current Version",
                    "New Version",
                    "Notes",
                ],
            ]
            table = terminaltables.AsciiTable(table_data)
            for filename in dry_run_tasks:
                result = serialisation_utils.json_loads(open(filename, "r").read())
                table_data.append(
                    [
                        result.get("effect"),
                        f'Launch:{result.get("params").get("launch_name")}'
                        if result.get("params").get("launch_name")
                        else f'Stack:{result.get("params").get("stack_name")}',
                        result.get("params").get("account_id"),
                        result.get("params").get("region"),
                        result.get("current_version"),
                        result.get("new_version"),
                        result.get("notes"),
                    ]
                )
            click.echo(table.table)
        else:
            table_data = [
                ["Action", "Params", "Duration"],
            ]
            table = terminaltables.AsciiTable(table_data)
            for filename in glob("results/success/*.json") + glob(
                "results/failure/*.json"
            ):
                result_contents = open(filename, "r").read()
                result = serialisation_utils.json_loads(result_contents)
                params = result.get("params_for_results")
                if not params.get("task_reference"):
                    params["task_reference"] = result.get("task_params").get(
                        "task_reference"
                    )
                if should_use_eventbridge:
                    if result.get("task_params"):
                        del result["task_params"]
                    entries.append(
                        {
                            "Source": constants.SERVICE_CATALOG_PUPPET_EVENT_SOURCE,
                            "Resources": [],
                            "DetailType": result.get("task_type"),
                            "Detail": json.dumps(result),
                            "EventBusName": constants.EVENT_BUS_IN_SPOKE_NAME
                            if execution_mode == constants.EXECUTION_MODE_SPOKE
                            else constants.EVENT_BUS_NAME,
                        }
                    )

                params = yaml.safe_dump(params)

                table_data.append(
                    [result.get("task_type"), params, result.get("duration"),]
                )
            click.echo(table.table)
            for filename in glob("results/failure/*.json"):
                result = serialisation_utils.json_loads(open(filename, "r").read())
                params = result.get("params_for_results")
                if should_forward_failures_to_opscenter:
                    title = f"{result.get('task_type')} failed: {params.get('task_reference')}"
                    logging.info(f"Sending failure to opscenter: {title}")
                    operational_data = dict(
                        codebuild_id=dict(Value=codebuild_id, Type="SearchableString")
                    )

                    for param_name in constants.PARAMETERS_TO_TRY_AS_OPERATIONAL_DATA:
                        if params.get(param_name):
                            operational_data[param_name] = {
                                "Value": json.dumps(
                                    params.get(param_name), default=str
                                ),
                                "Type": "SearchableString",
                            }
                    description = "\n".join(result.get("exception_stack_trace"))[-1024:]
                    try:
                        ssm_client.create_ops_item(
                            Title=title,
                            Description=description,
                            OperationalData=operational_data,
                            Priority=1,
                            Source=constants.SERVICE_CATALOG_PUPPET_OPS_CENTER_SOURCE,
                            Tags=[
                                {
                                    "Key": "ServiceCatalogPuppet:Actor",
                                    "Value": "ops-item",
                                },
                            ],
                        )
                    except ssm_client.exceptions.OpsItemLimitExceededException:
                        logging.error(
                            f"OpsItem: {title} creation failed due to OpsItemLimitExceededException. OperationalData: {operational_data}"
                        )
                if "RunDeployInSpoke" in filename:
                    click.echo(
                        colorclass.Color(
                            "{red}" + result.get("task_type") + " failed{/red}"
                        )
                    )
                    click.echo(
                        f"{yaml.safe_dump({'parameters': result.get('task_params')})}"
                    )
                    click.echo("\n".join(result.get("exception_stack_trace")))
                    click.echo("")

            if should_use_eventbridge:
                logging.info(f"Sending {len(entries)} events to eventbridge")
                with betterboto_client.CrossAccountClientContextManager(
                    "events",
                    config.get_puppet_role_arn(current_account_id),
                    f"{current_account_id}-{config.get_puppet_role_name()}",
                ) as events:
                    batches = generate_batches(entries)
                    for batch in batches:
                        events.put_events(Entries=batch)
                        time.sleep(1)
                logging.info(f"Finished sending {len(entries)} events to eventbridge")

    if on_complete_url:
        logger.info(f"About to post results")
        if not has_failures:
            result = dict(
                Status="SUCCESS",
                Reason=f"All tasks run with success: {codebuild_id}",
                UniqueId=codebuild_id.replace(":", "").replace("-", ""),
                Data=f"{codebuild_id}",
            )
        else:
            result = dict(
                Status="FAILURE",
                Reason=f"All tasks did not run with success: {codebuild_id}",
                UniqueId=codebuild_id.replace(":", "").replace("-", ""),
                Data=f"{codebuild_id}",
            )
        req = urllib.request.Request(
            url=on_complete_url, data=json.dumps(result).encode(), method="PUT"
        )
        with urllib.request.urlopen(req) as f:
            pass
        logger.info(f.status)
        logger.info(f.reason)

    if running_exploded:
        pass
    else:
        if has_spoke_failures or has_failures:
            sys.exit(1)
        else:
            sys.exit(0)


def generate_batches(entries):
    batches = list()
    current_batch = list()
    batches.append(current_batch)
    current_batch_size = 0
    batch_size_limit = 256000
    for e in entries:
        current_entry_size = sys.getsizeof(e.get("Source"))
        current_entry_size += sys.getsizeof(e.get("DetailType"))
        current_entry_size += sys.getsizeof(
            serialisation_utils.json_dumps(e.get("Detail"))
        )

        if (
            current_batch_size + current_entry_size > batch_size_limit
            or len(current_batch) >= 10
        ):
            current_batch_size = 0
            current_batch = list()
            batches.append(current_batch)

        current_batch.append(e)
        current_batch_size += current_entry_size

    return batches


def run_tasks_for_bootstrap_spokes_in_ou(tasks_to_run, num_workers):
    for result_type in [
        "start",
        "failure",
        "success",
        "timeout",
        "process_failure",
        "processing_time",
        "broken_task",
        "traces",
    ]:
        os.makedirs(Path(constants.RESULTS_DIRECTORY) / result_type)

    run_result = luigi.build(
        tasks_to_run,
        local_scheduler=True,
        detailed_summary=True,
        workers=num_workers,
        log_level=os.environ.get("LUIGI_LOG_LEVEL", constants.LUIGI_DEFAULT_LOG_LEVEL),
    )

    for filename in glob("results/failure/*.json"):
        result = serialisation_utils.json_loads(open(filename, "r").read())
        click.echo(
            colorclass.Color("{red}" + result.get("task_type") + " failed{/red}")
        )
        click.echo(f"{yaml.safe_dump({'parameters': result.get('task_params')})}")
        click.echo("\n".join(result.get("exception_stack_trace")))
        click.echo("")
    exit_status_codes = {
        LuigiStatusCode.SUCCESS: 0,
        LuigiStatusCode.SUCCESS_WITH_RETRY: 0,
        LuigiStatusCode.FAILED: 1,
        LuigiStatusCode.FAILED_AND_SCHEDULING_FAILED: 2,
        LuigiStatusCode.SCHEDULING_FAILED: 3,
        LuigiStatusCode.NOT_RUN: 4,
        LuigiStatusCode.MISSING_EXT: 5,
    }

    sys.exit(exit_status_codes.get(run_result.status))
