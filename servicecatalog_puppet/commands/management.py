#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import glob
from servicecatalog_puppet import serialisation_utils
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import cfn_tools
import click
import terminaltables
import yaml
from betterboto import client as betterboto_client
from jinja2 import Template

from servicecatalog_puppet import (
    constants,
    config,
    asset_helpers,
    viz_template,
    print_utils,
)


def upload_config(config):
    with betterboto_client.ClientContextManager("ssm") as ssm:
        ssm.put_parameter(
            Name=constants.CONFIG_PARAM_NAME,
            Type="String",
            Value=yaml.safe_dump(config),
            Overwrite=True,
        )
    click.echo("Uploaded config")


def seed(complexity, p):
    example = "manifest-{}.yaml".format(complexity)
    shutil.copy2(
        asset_helpers.resolve_from_site_packages(
            os.path.sep.join(["manifests", example])
        ),
        os.path.sep.join([p, "manifest.yaml"]),
    )


def list_resources():
    click.echo("# Framework resources")

    click.echo("## SSM Parameters used")
    click.echo(f"- {constants.CONFIG_PARAM_NAME}")
    click.echo(f"- {constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN}")

    for file in Path(__file__).parent.resolve().glob("*.template.yaml"):
        if "empty.template.yaml" == file.name:
            continue
        template_contents = Template(open(file, "r").read()).render()
        template = cfn_tools.load_yaml(template_contents)
        click.echo(f"## Resources for stack: {file.name.split('.')[0]}")
        table_data = [
            ["Logical Name", "Resource Type", "Name",],
        ]
        table = terminaltables.AsciiTable(table_data)
        for logical_name, resource in template.get("Resources").items():
            resource_type = resource.get("Type")
            name = "-"
            type_to_name = {
                "AWS::IAM::Role": "RoleName",
                "AWS::SSM::Parameter": "Name",
                "AWS::S3::Bucket": "BucketName",
                "AWS::CodePipeline::Pipeline": "Name",
                "AWS::CodeBuild::Project": "Name",
                "AWS::CodeCommit::Repository": "RepositoryName",
                "AWS::SNS::Topic": "TopicName",
                "AWS::SQS::Queue": "QueueName",
            }

            if type_to_name.get(resource_type) is not None:
                name = resource.get("Properties", {}).get(
                    type_to_name.get(resource_type), "Not Specified"
                )
                if not isinstance(name, str):
                    name = cfn_tools.dump_yaml(name)

            table_data.append([logical_name, resource_type, name])

        click.echo(table.table)
    click.echo(f"n.b. AWS::StackName evaluates to {constants.BOOTSTRAP_STACK_NAME}")


def set_config_value(name, value, is_a_boolean=True):
    with betterboto_client.ClientContextManager(
        "ssm", region_name=constants.HOME_REGION
    ) as ssm:
        try:
            response = ssm.get_parameter(Name=constants.CONFIG_PARAM_NAME)
            config = yaml.safe_load(response.get("Parameter").get("Value"))
        except ssm.exceptions.ParameterNotFound:
            config = {}

        if name == "regions":
            config["regions"] = value if len(value) > 1 else value[0].split(",")
        else:
            if is_a_boolean:
                config[name] = value.upper() == "TRUE"
            else:
                config[name] = value

        upload_config(config)


def set_named_config_value(name, value):
    with betterboto_client.ClientContextManager(
        "ssm", region_name=constants.HOME_REGION
    ) as ssm:
        ssm.put_parameter(
            Name=name, Type="String", Value=value, Overwrite=True,
        )
        click.echo("Uploaded named config")


def handle_action_execution_detail(puppet_account_id, action_execution_detail):
    action_type_id = action_execution_detail.get("input").get("actionTypeId")
    if (
        action_type_id.get("category") == "Build"
        and action_type_id.get("owner") == "AWS"
        and action_type_id.get("provider") == "CodeBuild"
    ):
        external_execution_id = (
            action_execution_detail.get("output")
            .get("executionResult")
            .get("externalExecutionId")
        )

        with betterboto_client.ClientContextManager(
            "codebuild", region_name=config.get_home_region(puppet_account_id)
        ) as codebuild:
            builds = codebuild.batch_get_builds(ids=[external_execution_id]).get(
                "builds"
            )
            build = builds[0]
            log_details = build.get("logs")
            with betterboto_client.ClientContextManager(
                "logs", region_name=config.get_home_region(puppet_account_id)
            ) as logs:
                project_name = (
                    action_execution_detail.get("input")
                    .get("configuration")
                    .get("ProjectName")
                )
                action_execution_id = action_execution_detail.get("actionExecutionId")
                output_file_name = f"log-{project_name}--{action_execution_id}.log"
                with open(output_file_name, "w",) as f:
                    params = {
                        "logGroupName": log_details.get("groupName"),
                        "logStreamName": log_details.get("streamName"),
                        "startFromHead": True,
                    }
                    has_more_logs = True
                    while has_more_logs:
                        get_log_events_response = logs.get_log_events(**params)
                        if (len(get_log_events_response.get("events"))) > 0:
                            params["nextToken"] = get_log_events_response.get(
                                "nextForwardToken"
                            )
                        else:
                            has_more_logs = False
                            if params.get("nextToken"):
                                del params["nextToken"]
                        for e in get_log_events_response.get("events"):
                            d = datetime.utcfromtimestamp(
                                e.get("timestamp") / 1000
                            ).strftime("%Y-%m-%d %H:%M:%S")
                            f.write(f"{d} : {e.get('message')}")


def export_puppet_pipeline_logs(execution_id, puppet_account_id):
    with betterboto_client.ClientContextManager(
        "codepipeline", region_name=config.get_home_region(puppet_account_id)
    ) as codepipeline:
        action_execution_details = codepipeline.list_action_executions(
            pipelineName=constants.PIPELINE_NAME,
            filter={"pipelineExecutionId": execution_id},
        ).get("actionExecutionDetails")

        for action_execution_detail in action_execution_details:
            handle_action_execution_detail(puppet_account_id, action_execution_detail)


def get_data_for_viz(codebuild_build_id, output_file_name_prefix):
    with betterboto_client.ClientContextManager("codebuild") as codebuild:
        build = codebuild.batch_get_builds(ids=[codebuild_build_id]).get("builds")[0]
        location = build.get("artifacts").get("location").split(":")
        bucket = location[5].split("/")[0]
        key = location[5].replace(f"{bucket}/", "")
        zip_file_location = f"{output_file_name_prefix}.zip"
        if os.path.exists(zip_file_location):
            print(f"Found zip file, skipping download")
        else:
            print(f"Downloading zip file")
            with betterboto_client.ClientContextManager("s3") as s3:
                print(f"getting {bucket} {key}")
                s3.download_file(Bucket=bucket, Key=key, Filename=zip_file_location)
        if os.path.exists(output_file_name_prefix):
            print(f"Found output folder, skipping unzip")
        else:
            print(f"Unziping")
            os.makedirs(output_file_name_prefix)
            with zipfile.ZipFile(zip_file_location, "r") as zip_ref:
                zip_ref.extractall(output_file_name_prefix)
    return f"{output_file_name_prefix}/results"


def generate_data_for_viz(path_to_results, group_by_pid):
    results = list()
    groups = dict()
    time_format = "%Y-%m-%d %H:%M:%S"
    earliest_time = datetime.strptime("4022-09-14 00:54:33", time_format)
    latest_time = datetime.strptime("2000-09-14 00:54:33", time_format)
    for starter in glob.glob(f"{path_to_results}/start/*.json"):
        start = serialisation_utils.json_loads(open(starter, "r").read())
        name = os.path.basename(starter)
        end = None
        task_id = name.replace(".json", "")
        task_id = "-".join(task_id.split("-")[1:])
        processing_time = dict(duration="unknown")

        if os.path.exists(f"{path_to_results}/success/{name}"):
            result = "success"
            end = serialisation_utils.json_loads(
                open(f"{path_to_results}/success/{name}", "r").read()
            )
        elif os.path.exists(f"{path_to_results}/failure/{name}"):
            result = "failure"
            end = serialisation_utils.json_loads(
                open(f"{path_to_results}/failure/{name}", "r").read()
            )

        if os.path.exists(f"{path_to_results}/processing_time/{name}"):
            processing_time = serialisation_utils.json_loads(
                open(f"{path_to_results}/processing_time/{name}", "r").read()
            )

        if end:
            body = ""
            starting_time = start.get("datetime")
            ending_time = end.get("datetime")
            pid = start.get("pid")
            groups[pid] = dict(id=pid, content=pid, value=pid,)
            for name2, value2 in start.get("params_for_results", {}).items():
                body += f"<b>{name2}</b>:{value2}<br />"
            body += f"<b>pid</b>:{pid}<br />"
            body += f"<b>start</b>:{starting_time}<br />"
            body += f"<b>end</b>:{ending_time}<br />"
            body += f"<b>duration</b>:{processing_time.get('duration')}<br />"
            content = f"""<h2>{task_id}</h2><dl>{body}</dl>"""
            task_type = task_id.split("_")[0]
            class_name = f"{result} {task_type}"

            starting_time = datetime.strptime(starting_time, time_format)
            ending_time = datetime.strptime(ending_time, time_format)

            if starting_time < earliest_time:
                earliest_time = starting_time

            if ending_time > latest_time:
                latest_time = ending_time

            if group_by_pid:
                d = dict(
                    id=task_id,
                    group=pid,
                    content=task_id,
                    title=content,
                    start=start.get("datetime"),
                    end=end.get("datetime"),
                    className=class_name,
                )
            else:
                d = dict(
                    id=task_id,
                    content=task_id,
                    title=content,
                    start=start.get("datetime"),
                    end=end.get("datetime"),
                    className=class_name,
                )
            results.append(d)
        else:
            print_utils.warn(f"Did not find an end for {name}")

    earliest_time = earliest_time - timedelta(minutes=2)
    latest_time = latest_time + timedelta(minutes=2)
    groups = list(groups.values())
    return (
        results,
        groups,
        earliest_time.strftime(time_format),
        latest_time.strftime(time_format),
    )


def export_deploy_viz(codebuild_execution_id, group_by_pid, puppet_account_id):
    output_file_name_prefix = codebuild_execution_id.split(":")[1]
    path_to_results = get_data_for_viz(codebuild_execution_id, output_file_name_prefix)
    results, groups, start, end = generate_data_for_viz(path_to_results, group_by_pid)
    if group_by_pid:
        params = "container, items, groups, options"
    else:
        params = "container, items, options"
    output = viz_template.CONTENT.format(
        DATASET=results, START=start, END=end, GROUPS=groups, PARAMS=params,
    )
    f = open(f"{output_file_name_prefix}.html", "w")
    f.write(output)
    f.close()


def generate_data_for_traces(path_to_results):
    results = list()
    for f in glob.glob(f"{path_to_results}/traces/*.json"):
        results.append(open(f, "r").read())
    return f'{{"traceEvents": [{",".join(results)}]}}'


def export_traces(codebuild_execution_id, puppet_account_id):
    bucket = f"sc-puppet-log-store-{puppet_account_id}"
    key_prefix = f"{codebuild_execution_id}/traces"

    results = list()
    with betterboto_client.ClientContextManager("s3") as s3:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=key_prefix,):
            print("new page", len(page.get("Contents", [])))
            for obj in page.get("Contents", []):
                key = obj.get("Key")
                results.append(
                    s3.get_object(Bucket=bucket, Key=key)
                    .get("Body")
                    .read()
                    .decode("utf-8")
                )

    traces = f'{{"traceEvents": [{",".join(results)}]}}'
    with open(f"{codebuild_execution_id.split('/')[-1]}-traces.json", "w") as f:
        f.write(traces)
