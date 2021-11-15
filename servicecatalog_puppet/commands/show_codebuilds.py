#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import operator

from betterboto import client as betterboto_client
import logging
import click
from servicecatalog_puppet import constants

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def get_codebuild_build_ids_for(codebuild_project_name, limit):
    codebuild_ids = list()
    with betterboto_client.ClientContextManager("codebuild") as codebuild:
        paginator = codebuild.get_paginator("list_builds_for_project")
        iterator = paginator.paginate(
            projectName=codebuild_project_name, sortOrder="DESCENDING",
        )
        for page in iterator:
            for i in page["ids"]:
                codebuild_ids.append(i)
                if len(codebuild_ids) == limit:
                    return codebuild_ids
    return codebuild_ids


def get_codebuild_build_ids(filter, limit):
    codebuild_build_list = []
    logger.info(f"Getting all Build Ids for CodeBuild project")
    if filter == "none":
        codebuild_build_list += get_codebuild_build_ids_for(
            constants.FULL_RUN_CODEBUILD_PROJECT_NAME, limit
        )
        codebuild_build_list += get_codebuild_build_ids_for(
            constants.SINGLE_ACCOUNT_RUN_CODEBUILD_PROJECT_NAME, limit
        )
    elif filter == "full-runs":
        codebuild_build_list += get_codebuild_build_ids_for(
            constants.FULL_RUN_CODEBUILD_PROJECT_NAME, limit
        )
    elif filter == "single-runs":
        codebuild_build_list += get_codebuild_build_ids_for(
            constants.SINGLE_ACCOUNT_RUN_CODEBUILD_PROJECT_NAME, limit
        )
    return codebuild_build_list


def get_build_info(build_id_list: list):
    """
    Returns the CodeBuild build information for the supplied CodeBuild build IDds.

        Parameters:
            build_id_list (list): List of CodeBuild build Ids
        
        Returns:
            build_info (list): List of dict objects with the information for each of the supplied build Ids
    """
    build_info = []
    logger.info(f"Getting information for {len(build_id_list)} builds")
    while len(build_id_list) > 0:
        logger.info(f"list length {len(build_id_list)}")
        inner_build_list = build_id_list[:50]

        with betterboto_client.ClientContextManager("codebuild") as codebuild:
            response = codebuild.batch_get_builds(ids=inner_build_list)

            for build in response["builds"]:
                duration = build["endTime"] - build["startTime"]
                inner_response_dict = {
                    "id": build["id"],
                    "start": build["startTime"],
                    "duration_in_seconds": str(round(duration.total_seconds())),
                    "status": build["buildStatus"],
                }
                build_info.append(inner_response_dict)
            del build_id_list[:50]
    return build_info


def write_csv(build_details):
    """
    Writes a CSV file with the build information from the supplied list

        Parameters:
            build_details (list): List of dict objects with the information for each build Id
            file_name (str): Name of the CSV file to create
    """
    logger.info(f"Writing output to CSV")
    results = [",".join(["id", "startTime", "duration_in_seconds", "status"])]
    for build in build_details:
        results.append(
            ",".join(
                [
                    build["id"],
                    build["start"].strftime("%d/%m/%Y %H:%M:%S"),
                    build["duration_in_seconds"],
                    build["status"],
                ]
            )
        )
    return "\n".join(results)


def sort_and_trim(what, limit):
    result = sorted(what, key=operator.itemgetter("start"), reverse=True)
    return result[:limit]


def show_codebuilds(filter, limit, format):
    """
    Exports the CodeBuild job statistics to CSV for the single account Puppet execution
    """
    build_ids = get_codebuild_build_ids(filter, limit)
    build_details_single = get_build_info(build_ids)
    result = sort_and_trim(build_details_single, limit)
    if format == "csv":
        click.echo(write_csv(result))
    elif format == "json":
        click.echo(json.dumps(result, indent=4, default=str))
