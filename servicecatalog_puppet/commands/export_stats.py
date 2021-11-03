#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# Define Imports
import boto3
from botocore.exceptions import ClientError 
import logging 
import sys 
import traceback 
import os 
import json 
from datetime import datetime 
import csv 
from itertools import islice
from servicecatalog_puppet import constants

# Static Variables
CODEBUILD_PROJECT_FULL = 'servicecatalog-puppet-deploy'
CODEBUILD_PROJECT_SINGLE = 'servicecatalog-puppet-single-account-run'
OUTPUT_PATH_FULL = './build_details_full.csv'
OUTPUT_PATH_SINGLE = './build_details_single.csv'

# Instantiate AWS client objects
cbClient = boto3.client('codebuild') 

# Instantiate Logger 
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_exception(exception_type, exception_value, exception_traceback):
    """
    Function to create a JSON object containing exception details. 
    This can then be logged as one line to the logger object.
    """
    traceback_string = traceback.format_exception(exception_type, exception_value, exception_traceback)
    err_msg = json.dumps({"errorType": exception_type.__name__, "errorMessage": str(exception_value), "stackTrace": traceback_string})
    logger.error(err_msg)

def get_codebuild_build_ids(project_name: str):
    """
    Returns the CodeBuild build Ids for a CodeBuild Project.

        Parameters:
            project_name (str): Name of the CodeBuild project
        
        Returns:
            codebuild_build_list (list): List of CodeBuild Build Ids for a CodeBuild Project
    """
    codebuild_build_list = []
    logger.info(f"Getting all Build Ids for CodeBuild project {project_name}")
    try:
        paginator = cbClient.get_paginator('list_builds_for_project')
        iterator = paginator.paginate(
            projectName=project_name
        )

        for page in iterator:
            for id in page['ids']:
                codebuild_build_list.append(id)
    except:
        log_exception(*sys.exc_info())
        raise RuntimeError(f"Failed to list all CodeBuild build Ids")
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

    try:
        while len(build_id_list) > 0:
            logger.info(f"list length {len(build_id_list)}")
            inner_build_list = build_id_list[:50]

            response = cbClient.batch_get_builds(
                ids=inner_build_list
            )

            for build in response['builds']:
                duration = build['endTime'] - build['startTime']
                inner_response_dict = {
                    "id": build['id'],
                    "start": build['startTime'].strftime("%d/%m/%Y %H:%M"),
                    "duration": duration.total_seconds(),
                    "status": build['buildStatus']
                }
                build_info.append(inner_response_dict)
            del build_id_list[:50]
    except:
        log_exception(*sys.exc_info())
        raise RuntimeError(f"Failed to process all CodeBuild Build Ids")
    return build_info

def write_csv(build_details: list, file_name: str):
    """
    Writes a CSV file with the build information from the supplied list

        Parameters:
            build_details (list): List of dict objects with the information for each build Id
            file_name (str): Name of the CSV file to create
    """
    logger.info(f"Writing output to CSV")
    header = ['id', 'startTime', 'duration', 'status']
    try:
        if os.path.isfile(file_name):
            os.remove(file_name)
        with open(file_name, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for build in build_details:
                data = [build['id'], build['start'], build['duration'], build['status']]
                writer.writerow(data)
        logger.info(f"Successfully wrote CSV data to {file_name}")
    except:
        log_exception(*sys.exc_info())
        raise RuntimeError(f"Failed to write output to CSV")

def export_full_stats():
    """
    Exports the CodeBuild job statistics to CSV for the full Puppet execution
    This includes single-account run data as well.
    """
    build_id_list_full = get_codebuild_build_ids(constants.CODEBUILD_PROJECT_NAME_FULL_PIPELINE)
    build_details_full = get_build_info(build_id_list_full)
    write_csv(build_details_full, constants.CODEBUILD_STATS_OUTPUT_PATH_FULL_PIPELINE)

def export_singleaccount_stats():
    """
    Exports the CodeBuild job statistics to CSV for the single account Puppet execution
    """
    build_id_list_single = get_codebuild_build_ids(constants.CODEBUILD_PROJECT_NAME_SINGLE_ACCOUNT)
    build_details_single = get_build_info(build_id_list_single)
    write_csv(build_details_single, constants.CODEBUILD_STATS_OUTPUT_PATH_SINGLE_ACCOUNT)
