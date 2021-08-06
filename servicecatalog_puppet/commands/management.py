#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
import shutil
from datetime import datetime
from pathlib import Path

import cfn_tools
import click
import terminaltables
import yaml
from betterboto import client as betterboto_client
from jinja2 import Template

from servicecatalog_puppet import constants, config, asset_helpers


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


def set_config_value(name, value):
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
            config[name] = value.upper() == "TRUE"

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
                with open(
                    f"log-{action_execution_detail.get('input').get('configuration').get('ProjectName')}.log",
                    "w",
                ) as f:
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
