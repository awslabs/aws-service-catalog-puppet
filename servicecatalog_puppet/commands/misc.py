#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import time
import traceback
import urllib

import click
from betterboto import client as betterboto_client

from servicecatalog_puppet import aws, config, constants


logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def cli(info, info_line_numbers):
    boto_level = os.environ.get("BOTO_LOG_LEVEL", logging.CRITICAL)

    logging.getLogger("boto").setLevel(boto_level)
    logging.getLogger("boto3").setLevel(boto_level)
    logging.getLogger("botocore").setLevel(boto_level)
    logging.getLogger("urllib3").setLevel(boto_level)

    luigi_level = os.environ.get("LUIGI_LOG_LEVEL", logging.CRITICAL)
    logging.getLogger("luigi").setLevel(luigi_level)

    if info:
        logging.basicConfig(
            format="%(levelname)s %(processName)s %(threadName)s %(message)s",
            level=logging.INFO,
        )
    if info_line_numbers:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(processName)s %(threadName)s [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d:%H:%M:%S",
            level=logging.INFO,
        )

    if info or info_line_numbers:
        logging.getLogger(constants.PUPPET_LOGGER_NAME).setLevel(logging.INFO)

    if os.environ.get("PUPPET_LOG_LEVEL"):
        logging.getLogger(constants.PUPPET_LOGGER_NAME).setLevel(
            os.environ.get("PUPPET_LOG_LEVEL")
        )


def wait_for_code_build_in(iam_role_arns):
    cross_accounts = []
    index = 0
    for role in iam_role_arns:
        cross_accounts.append((role, "waiting-for-code-build-{}".format(index)))
        index += 1

    with betterboto_client.CrossMultipleAccountsClientContextManager(
        "codebuild", cross_accounts
    ) as codebuild:
        while True:
            try:
                result = codebuild.list_projects()
                logger.info(f"Was able to list projects: {result}")
                break
            except Exception as e:
                logger.error("type error: " + str(e))
                logger.error(traceback.format_exc())


def wait_for_cloudformation_in(iam_role_arns):
    cross_accounts = []
    index = 0
    for role in iam_role_arns:
        cross_accounts.append((role, "waiting-for-cloudformation-{}".format(index)))
        index += 1

    with betterboto_client.CrossMultipleAccountsClientContextManager(
        "cloudformation", cross_accounts
    ) as cloudformation:
        while True:
            try:
                result = cloudformation.list_stacks()
                logger.info(f"Was able to list stacks: {result}")
                break
            except Exception as e:
                logger.error("type error: " + str(e))
                logger.error(traceback.format_exc())


def wait_for_run_to_complete(pipeline_execution_id, on_complete_url: str) -> bool:
    while True:
        time.sleep(5)
        with betterboto_client.ClientContextManager("codepipeline") as codepipeline:
            while True:
                time.sleep(10)
                pipelineExecution = codepipeline.get_pipeline_execution(
                    pipelineName=constants.PIPELINE_NAME,
                    pipelineExecutionId=pipeline_execution_id,
                ).get("pipelineExecution")
                status = pipelineExecution.get("status")
                click.echo(f"Current status (A): {status}")
                if status in [
                    "Cancelled",
                    "Stopped",
                    "Succeeded",
                    "Superseded",
                    "Failed",
                ]:
                    succeeded = status in ["Succeeded"]
                    if on_complete_url:
                        logger.info(f"About to post results")
                        if succeeded:
                            result = dict(
                                Status="SUCCESS",
                                Reason=f"All tasks run with success: {pipeline_execution_id}",
                                UniqueId=pipeline_execution_id.replace(":", "").replace(
                                    "-", ""
                                ),
                                Data=f"{pipeline_execution_id}",
                            )
                        else:
                            result = dict(
                                Status="FAILURE",
                                Reason=f"All tasks did not run with success: {pipeline_execution_id}",
                                UniqueId=pipeline_execution_id.replace(":", "").replace(
                                    "-", ""
                                ),
                                Data=f"{pipeline_execution_id}",
                            )
                        req = urllib.request.Request(
                            url=on_complete_url,
                            data=json.dumps(result).encode(),
                            method="PUT",
                        )
                        with urllib.request.urlopen(req) as f:
                            pass
                        logger.info(f.status)
                        logger.info(f.reason)

                    return succeeded


def run(what, tail):
    pipelines = {"puppet": constants.PIPELINE_NAME}
    pipeline_name = pipelines.get(what)
    pipeline_execution_id = aws.run_pipeline(pipeline_name, tail)
    click.echo(
        f"https://{os.environ.get('AWS_DEFAULT_REGION')}.console.aws.amazon.com/codesuite/codepipeline/pipelines/{pipeline_name}/executions/{pipeline_execution_id}/timeline"
    )


def uninstall(puppet_account_id):
    with betterboto_client.ClientContextManager(
        "cloudformation", region_name=config.get_home_region(puppet_account_id)
    ) as cloudformation:
        cloudformation.ensure_deleted(StackName=constants.BOOTSTRAP_STACK_NAME)
