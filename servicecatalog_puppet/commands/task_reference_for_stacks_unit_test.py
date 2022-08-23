#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os
from unittest import mock as mocker
from unittest.mock import call

puppet_account = {
    "account_id": "${AWS::PuppetAccountId}",
    "name": "puppet-account",
    "default_region": "eu-west-1",
    "regions_enabled": [
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "us-west-1",
        "us-east-1",
    ],
    "tags": ["role:sct",],
}

account_from_hundred = {
    "account_id": "012345678910",
    "name": "hundred",
    "default_region": "eu-west-1",
    "regions_enabled": [
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "us-west-1",
        "us-east-1",
    ],
    "tags": ["group:hundred",],
}

stack_sleeper = {
    "execution": "hub",
    "name": "sleeper",
    "version": "v1",
    "capabilities": ["CAPABILITY_IAM"],
    "parameters": {"PrincipalOrgID": {"default": "o-sw3edla4pd"},},
    "deploy_to": {"tags": [{"tag": "role:sct", "regions": "enabled_regions"},]},
}
sleep = {
    "execution": "hub",
    "name": "sleep",
    "version": "v1",
    "capabilities": ["CAPABILITY_IAM"],
    "parameters": {
        "Duration": {"default": "10"},
        "SleeperCustomResourceArn": {
            "cloudformation_stack_output": {
                "account_id": "${AWS::PuppetAccountId}",
                "region": "${AWS::Region}",
                "stack_name": "sleeper",
                "output_key": "SleeperFunctionArn",
            }
        },
    },
    "depends_on": [{"name": "sleeper", "type": "stack", "affinity": "region",},],
    "deploy_to": {"tags": [{"tag": "group:hundred", "regions": "enabled_regions"},]},
}
sleep_spoke = {
    "execution": "spoke",
    "name": "sleep",
    "version": "v1",
    "capabilities": ["CAPABILITY_IAM"],
    "parameters": {
        "Duration": {"default": "10"},
        "SleeperCustomResourceArn": {
            "cloudformation_stack_output": {
                "account_id": "${AWS::PuppetAccountId}",
                "region": "${AWS::Region}",
                "stack_name": "sleeper",
                "output_key": "SleeperFunctionArn",
            }
        },
    },
    "depends_on": [{"name": "sleeper", "type": "stack", "affinity": "region",},],
    "deploy_to": {"tags": [{"tag": "group:hundred", "regions": "enabled_regions"},]},
}
stack_generate_complete_task_reference_expected_result = {
    "all_tasks": {
        "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1": {
            "stack_name": "sleeper",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "hub",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [],
            "account_id": "${AWS::PuppetAccountId}",
            "region": "eu-west-1",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleeper",
            "manifest_account_id": "${AWS::PuppetAccountId}",
            "section_name": "stacks",
            "item_name": "sleeper",
            "dependencies_by_reference": ["get-template-from-s3-stacks-sleeper"],
            "reverse_dependencies_by_reference": [
                "stacks_sleep_012345678910-eu-west-1"
            ],
            "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1",
            "get_s3_template_ref": "get-template-from-s3-stacks-sleeper",
        },
        "get-template-from-s3-stacks-sleeper": {
            "task_reference": "get-template-from-s3-stacks-sleeper",
            "execution": "hub",
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "region": "eu-west-1",
            "version_id": "",
            "puppet_account_id": "012345678910",
            "account_id": "012345678910",
            "dependencies_by_reference": [],
            "reverse_dependencies_by_reference": [
                "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1"
            ],
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleeper",
            "manifest_account_id": "${AWS::PuppetAccountId}",
            "section_name": "get-template-from-s3",
        },
        "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-2": {
            "stack_name": "sleeper",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "hub",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [],
            "account_id": "${AWS::PuppetAccountId}",
            "region": "eu-west-2",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleeper",
            "manifest_account_id": "${AWS::PuppetAccountId}",
            "section_name": "stacks",
            "item_name": "sleeper",
            "dependencies_by_reference": [],
            "reverse_dependencies_by_reference": [
                "stacks_sleep_012345678910-eu-west-2"
            ],
            "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-2",
        },
        "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-3": {
            "stack_name": "sleeper",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "hub",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [],
            "account_id": "${AWS::PuppetAccountId}",
            "region": "eu-west-3",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleeper",
            "manifest_account_id": "${AWS::PuppetAccountId}",
            "section_name": "stacks",
            "item_name": "sleeper",
            "dependencies_by_reference": [],
            "reverse_dependencies_by_reference": [
                "stacks_sleep_012345678910-eu-west-3"
            ],
            "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-3",
        },
        "stacks_sleeper_${AWS::PuppetAccountId}-us-west-1": {
            "stack_name": "sleeper",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "hub",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [],
            "account_id": "${AWS::PuppetAccountId}",
            "region": "us-west-1",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleeper",
            "manifest_account_id": "${AWS::PuppetAccountId}",
            "section_name": "stacks",
            "item_name": "sleeper",
            "dependencies_by_reference": [],
            "reverse_dependencies_by_reference": [
                "stacks_sleep_012345678910-us-west-1"
            ],
            "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-us-west-1",
        },
        "stacks_sleeper_${AWS::PuppetAccountId}-us-east-1": {
            "stack_name": "sleeper",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "hub",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [],
            "account_id": "${AWS::PuppetAccountId}",
            "region": "us-east-1",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleeper",
            "manifest_account_id": "${AWS::PuppetAccountId}",
            "section_name": "stacks",
            "item_name": "sleeper",
            "dependencies_by_reference": [],
            "reverse_dependencies_by_reference": [
                "stacks_sleep_012345678910-us-east-1"
            ],
            "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-us-east-1",
        },
        "stacks_sleep_012345678910-eu-west-1": {
            "stack_name": "sleep",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "spoke",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [
                {"name": "sleeper", "type": "stack", "affinity": "region"}
            ],
            "account_id": "012345678910",
            "region": "eu-west-1",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleep",
            "manifest_account_id": "012345678910",
            "section_name": "stacks",
            "item_name": "sleep",
            "dependencies_by_reference": [
                "get-template-from-s3-stacks-sleep",
                "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1",
            ],
            "reverse_dependencies_by_reference": [],
            "task_reference": "stacks_sleep_012345678910-eu-west-1",
            "get_s3_template_ref": "get-template-from-s3-stacks-sleep",
        },
        "get-template-from-s3-stacks-sleep": {
            "task_reference": "get-template-from-s3-stacks-sleep",
            "execution": "hub",
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "region": "eu-west-1",
            "version_id": "",
            "puppet_account_id": "012345678910",
            "account_id": "012345678910",
            "dependencies_by_reference": [],
            "reverse_dependencies_by_reference": [
                "stacks_sleep_012345678910-eu-west-1"
            ],
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleep",
            "manifest_account_id": "012345678910",
            "section_name": "get-template-from-s3",
        },
        "stacks_sleep_012345678910-eu-west-2": {
            "stack_name": "sleep",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "spoke",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [
                {"name": "sleeper", "type": "stack", "affinity": "region"}
            ],
            "account_id": "012345678910",
            "region": "eu-west-2",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleep",
            "manifest_account_id": "012345678910",
            "section_name": "stacks",
            "item_name": "sleep",
            "dependencies_by_reference": [
                "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-2"
            ],
            "reverse_dependencies_by_reference": [],
            "task_reference": "stacks_sleep_012345678910-eu-west-2",
        },
        "stacks_sleep_012345678910-eu-west-3": {
            "stack_name": "sleep",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "spoke",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [
                {"name": "sleeper", "type": "stack", "affinity": "region"}
            ],
            "account_id": "012345678910",
            "region": "eu-west-3",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleep",
            "manifest_account_id": "012345678910",
            "section_name": "stacks",
            "item_name": "sleep",
            "dependencies_by_reference": [
                "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-3"
            ],
            "reverse_dependencies_by_reference": [],
            "task_reference": "stacks_sleep_012345678910-eu-west-3",
        },
        "stacks_sleep_012345678910-us-west-1": {
            "stack_name": "sleep",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "spoke",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [
                {"name": "sleeper", "type": "stack", "affinity": "region"}
            ],
            "account_id": "012345678910",
            "region": "us-west-1",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleep",
            "manifest_account_id": "012345678910",
            "section_name": "stacks",
            "item_name": "sleep",
            "dependencies_by_reference": [
                "stacks_sleeper_${AWS::PuppetAccountId}-us-west-1"
            ],
            "reverse_dependencies_by_reference": [],
            "task_reference": "stacks_sleep_012345678910-us-west-1",
        },
        "stacks_sleep_012345678910-us-east-1": {
            "stack_name": "sleep",
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_IAM"],
            "ssm_param_outputs": [],
            "bucket": "sc-puppet-stacks-repository-012345678910",
            "key": None,
            "version_id": "",
            "execution": "spoke",
            "use_service_role": False,
            "puppet_account_id": "012345678910",
            "status": None,
            "requested_priority": 0,
            "dependencies": [
                {"name": "sleeper", "type": "stack", "affinity": "region"}
            ],
            "account_id": "012345678910",
            "region": "us-east-1",
            "manifest_section_name": "stacks",
            "manifest_item_name": "sleep",
            "manifest_account_id": "012345678910",
            "section_name": "stacks",
            "item_name": "sleep",
            "dependencies_by_reference": [
                "stacks_sleeper_${AWS::PuppetAccountId}-us-east-1"
            ],
            "reverse_dependencies_by_reference": [],
            "task_reference": "stacks_sleep_012345678910-us-east-1",
        },
    }
}


@mocker.patch("servicecatalog_puppet.config", new_callable=mocker.MagicMock())
@mocker.patch("builtins.open", new_callable=mocker.MagicMock())
def test_generate_complete_task_reference_for_simple_stack(open_mocked, config_mocked):
    # setup
    from servicecatalog_puppet.commands import task_reference
    from servicecatalog_puppet import manifest_utils

    f = mocker.MagicMock()
    puppet_account_id = "012345678910"
    manifest = manifest_utils.Manifest(
        dict(
            accounts=[puppet_account, account_from_hundred,],
            stacks=dict(sleeper=stack_sleeper,),
        )
    )
    expected_result = {
        "all_tasks": {
            "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": ["get-template-from-s3-stacks-sleeper"],
                "reverse_dependencies_by_reference": [],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                "get_s3_template_ref": "get-template-from-s3-stacks-sleeper",
            },
            "get-template-from-s3-stacks-sleeper": {
                "task_reference": "get-template-from-s3-stacks-sleeper",
                "execution": "hub",
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "region": "eu-west-1",
                "version_id": "",
                "puppet_account_id": "012345678910",
                "account_id": "012345678910",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "get-template-from-s3",
            },
            "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-2": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-2",
            },
            "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-3": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-3",
            },
            "stacks_sleeper_${AWS::PuppetAccountId}-us-west-1": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-us-west-1",
            },
            "stacks_sleeper_${AWS::PuppetAccountId}-us-east-1": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-us-east-1",
            },
        }
    }

    # exercise
    actual_result = task_reference.generate_complete_task_reference(
        f, puppet_account_id, manifest
    )

    # verify
    assert actual_result == expected_result


@mocker.patch("servicecatalog_puppet.config", new_callable=mocker.MagicMock())
@mocker.patch("builtins.open", new_callable=mocker.MagicMock())
def test_generate_complete_task_reference_for_stack(
    open_mocked, config_mocked,
):
    # setup
    from servicecatalog_puppet.commands import task_reference
    from servicecatalog_puppet import manifest_utils

    f = mocker.MagicMock()
    puppet_account_id = "012345678910"
    manifest = manifest_utils.Manifest(
        dict(
            accounts=[puppet_account, account_from_hundred,],
            stacks=dict(sleeper=stack_sleeper, sleep=sleep_spoke),
        )
    )
    expected_result = stack_generate_complete_task_reference_expected_result

    # exercise
    actual_result = task_reference.generate_complete_task_reference(
        f, puppet_account_id, manifest
    )

    # verify
    assert actual_result == expected_result


@mocker.patch("servicecatalog_puppet.config", new_callable=mocker.MagicMock())
@mocker.patch("builtins.open", new_callable=mocker.MagicMock())
def sstest_generate_hub_task_reference_for_stack_with_spoke_execution_mode(
    open_mocked, config_mocked
):
    # setup
    from servicecatalog_puppet.commands import task_reference
    from servicecatalog_puppet import manifest_utils

    f = mocker.MagicMock()
    puppet_account_id = "012345678910"
    new_name = "banana"
    expected_result = {
        "all_tasks": {
            "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": ["get-template-from-s3-stacks-sleeper"],
                "reverse_dependencies_by_reference": [
                    "stacks_sleep_012345678910-eu-west-1"
                ],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                "get_s3_template_ref": "get-template-from-s3-stacks-sleeper",
            },
            "get-template-from-s3-stacks-sleeper": {
                "task_reference": "get-template-from-s3-stacks-sleeper",
                "execution": "hub",
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "region": "eu-west-1",
                "version_id": "",
                "puppet_account_id": "012345678910",
                "account_id": "012345678910",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "get-template-from-s3",
            },
            "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-2": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "stacks_sleep_012345678910-eu-west-2"
                ],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-2",
            },
            "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-3": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "stacks_sleep_012345678910-eu-west-3"
                ],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-3",
            },
            "stacks_sleeper_${AWS::PuppetAccountId}-us-west-1": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "stacks_sleep_012345678910-us-west-1"
                ],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-us-west-1",
            },
            "stacks_sleeper_${AWS::PuppetAccountId}-us-east-1": {
                "stack_name": "sleeper",
                "launch_name": "",
                "stack_set_name": "",
                "capabilities": ["CAPABILITY_IAM"],
                "ssm_param_outputs": [],
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "version_id": "",
                "execution": "hub",
                "use_service_role": False,
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "stacks",
                "item_name": "sleeper",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "stacks_sleep_012345678910-us-east-1"
                ],
                "task_reference": "stacks_sleeper_${AWS::PuppetAccountId}-us-east-1",
            },
            "generate-manifest": {
                "puppet_account_id": "012345678910",
                "task_reference": "generate-manifest",
                "section_name": "generate-manifest",
                "dependencies_by_reference": [
                    "get-template-from-s3-stacks-sleep",
                    "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "stacks_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "stacks_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
            },
            "run-deploy-in-spoke_012345678910": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "account_id": "012345678910",
                "section_name": "run-deploy-in-spoke",
                "task_reference": "run-deploy-in-spoke_012345678910",
                "generate_manifest_ref": "generate-manifest",
                "dependencies_by_reference": [
                    "generate-manifest",
                    "get-template-from-s3-stacks-sleep",
                    "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "stacks_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "stacks_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "stacks_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
            },
            "get-template-from-s3-stacks-sleep": {
                "task_reference": "get-template-from-s3-stacks-sleep",
                "execution": "hub",
                "bucket": "sc-puppet-stacks-repository-012345678910",
                "key": None,
                "region": "eu-west-1",
                "version_id": "",
                "puppet_account_id": "012345678910",
                "account_id": "012345678910",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "stacks_sleep_012345678910-eu-west-1"
                ],
                "manifest_section_name": "stacks",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "get-template-from-s3",
            },
        }
    }

    # exercise
    actual_result = task_reference.generate_hub_task_reference(
        puppet_account_id,
        stack_generate_complete_task_reference_expected_result.get("all_tasks"),
        new_name,
    )

    # verify
    assert actual_result == expected_result
