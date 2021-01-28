import json
import os
import sys
import time
import urllib
from glob import glob
from pathlib import Path

import click
import colorclass
import luigi
import terminaltables
import yaml
from betterboto import client as betterboto_client
from colorclass import Color
from luigi import LuigiStatusCode

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.workflow import tasks

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_tasks(
    puppet_account_id,
    current_account_id,
    tasks_to_run,
    num_workers,
    is_dry_run=False,
    is_list_launches=None,
    execution_mode="hub",
    cache_invalidator="now",
    on_complete_url=None,
):
    codebuild_id = os.getenv("CODEBUILD_BUILD_ID", "LOCAL_BUILD")
    if is_list_launches:
        should_use_eventbridge = False
        should_forward_failures_to_opscenter = False
    else:
        should_use_eventbridge = (
            config.get_should_use_eventbridge(
                puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
            )
            and not is_dry_run
        )
        should_forward_failures_to_opscenter = (
            config.get_should_forward_failures_to_opscenter(
                puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
            )
            and not is_dry_run
        )

    ssm_client = None
    if should_forward_failures_to_opscenter:
        with betterboto_client.ClientContextManager("ssm") as ssm:
            ssm_client = ssm

    entries = []

    for result_type in [
        "failure",
        "success",
        "timeout",
        "process_failure",
        "processing_time",
        "broken_task",
    ]:
        os.makedirs(Path(constants.RESULTS_DIRECTORY) / result_type)

    logger.info(f"About to run workflow with {num_workers} workers")

    tasks.print_stats()

    should_use_shared_scheduler = config.get_should_use_shared_scheduler(
        puppet_account_id
    )

    build_params = dict(detailed_summary=True, workers=num_workers, log_level="INFO",)

    if should_use_shared_scheduler:
        os.system(constants.START_SHARED_SCHEDULER_COMMAND)
    else:
        build_params["local_scheduler"] = True

    logger.info(f"should_use_shared_scheduler: {should_use_shared_scheduler}")

    run_result = luigi.build(tasks_to_run, **build_params)

    exit_status_codes = {
        LuigiStatusCode.SUCCESS: 0,
        LuigiStatusCode.SUCCESS_WITH_RETRY: 0,
        LuigiStatusCode.FAILED: 1,
        LuigiStatusCode.FAILED_AND_SCHEDULING_FAILED: 2,
        LuigiStatusCode.SCHEDULING_FAILED: 3,
        LuigiStatusCode.NOT_RUN: 4,
        LuigiStatusCode.MISSING_EXT: 5,
    }

    if is_list_launches:
        if is_list_launches == "table":
            table = [
                [
                    "account_id",
                    "region",
                    "launch",
                    "portfolio",
                    "product",
                    "expected_version",
                    "actual_version",
                    "active",
                    "status",
                ]
            ]

            for filename in glob(
                f"output/ProvisionProductDryRunTask/**/{cache_invalidator}.json",
                recursive=True,
            ):
                result = json.loads(open(filename, "r").read())
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
                        result.get("params").get("launch_name"),
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
                result = json.loads(open(filename, "r").read())
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
                    "Launch",
                    "Account",
                    "Region",
                    "Current Version",
                    "New Version",
                    "Notes",
                ],
            ]
            table = terminaltables.AsciiTable(table_data)
            for filename in glob(
                f"output/TerminateProductDryRunTask/**/{cache_invalidator}.json",
                recursive=True,
            ):
                result = json.loads(open(filename, "r").read())
                table_data.append(
                    [
                        result.get("effect"),
                        result.get("params").get("launch_name"),
                        result.get("params").get("account_id"),
                        result.get("params").get("region"),
                        result.get("current_version"),
                        result.get("new_version"),
                        result.get("notes"),
                    ]
                )
            for filename in glob(
                f"output/ProvisionProductDryRunTask/**/{cache_invalidator}.json",
                recursive=True,
            ):
                result = json.loads(open(filename, "r").read())
                table_data.append(
                    [
                        result.get("effect"),
                        result.get("params").get("launch_name"),
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
            for filename in glob("results/processing_time/*.json"):
                result_contents = open(filename, "r").read()
                result = json.loads(result_contents)
                params = result.get("params_for_results")
                if should_use_eventbridge:
                    entries.append(
                        {
                            # 'Time': ,
                            "Source": constants.SERVICE_CATALOG_PUPPET_EVENT_SOURCE,
                            "Resources": [
                                # 'string',
                            ],
                            "DetailType": result.get("task_type"),
                            "Detail": result_contents,
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
                result = json.loads(open(filename, "r").read())
                params = result.get("params_for_results")
                if should_forward_failures_to_opscenter:
                    title = f"{result.get('task_type')} failed: {params.get('launch_name')} - {params.get('account_id')} - {params.get('region')}"
                    logging.info(f"Sending failure to opscenter: {title}")
                    operational_data = dict(
                        codebuild_id=dict(Value=codebuild_id, Type="SearchableString")
                    )
                    for param_name, param in params.items():
                        operational_data[param_name] = {
                            "Value": json.dumps(param, default=str),
                            "Type": "SearchableString",
                        }
                    description = "\n".join(result.get("exception_stack_trace"))[-1024:]
                    ssm_client.create_ops_item(
                        Title=title,
                        Description=description,
                        OperationalData=operational_data,
                        Priority=1,
                        Source=constants.SERVICE_CATALOG_PUPPET_OPS_CENTER_SOURCE,
                        Tags=[
                            {"Key": "ServiceCatalogPuppet:Actor", "Value": "ops-item"},
                        ],
                    )

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
                    for i in range(
                        0, len(entries), constants.EVENTBRIDGE_MAX_EVENTS_PER_CALL
                    ):
                        events.put_events(
                            Entries=entries[
                                i : i + constants.EVENTBRIDGE_MAX_EVENTS_PER_CALL
                            ]
                        )
                        time.sleep(1)
                logging.info(f"Finished sending {len(entries)} events to eventbridge")

    exit_status_code = exit_status_codes.get(run_result.status)
    if on_complete_url:
        logger.info(f"About to post results")
        if exit_status_code == 0:
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

    sys.exit(exit_status_code)


def run_tasks_for_bootstrap_spokes_in_ou(tasks_to_run, num_workers):
    for result_type in [
        "failure",
        "success",
        "timeout",
        "process_failure",
        "processing_time",
        "broken_task",
    ]:
        os.makedirs(Path(constants.RESULTS_DIRECTORY) / result_type)

    run_result = luigi.build(
        tasks_to_run,
        local_scheduler=True,
        detailed_summary=True,
        workers=num_workers,
        log_level="INFO",
    )

    for filename in glob("results/failure/*.json"):
        result = json.loads(open(filename, "r").read())
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
