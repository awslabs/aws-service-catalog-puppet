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

launch_sleeper = {
    "execution": "hub",
    "portfolio": "DepsRefactor5",
    "product": "sleeper5",
    "version": "v1",
    "capabilities": ["CAPABILITY_IAM"],
    "parameters": {"PrincipalOrgID": {"default": "o-sw3edla4pd"}},
    "deploy_to": {"tags": [{"tag": "role:sct", "regions": "enabled_regions"}]},
    "outputs": {
        "ssm": [
            {
                "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                "stack_output": "SleeperFunctionArn",
            }
        ]
    },
}

launch_sleep = {
    "execution": "hub",
    "portfolio": "DepsRefactor5",
    "product": "sleep5",
    "version": "v1",
    "deploy_to": {"tags": [{"tag": "group:hundred", "regions": "regions_enabled"}]},
    "parameters": {
        "Duration": {"default": "8"},
        "SleeperCustomResourceArn": {
            "ssm": {
                "name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                "path": "/sleeper/SleeperFunctionArn",
            }
        },
    },
    "depends_on": [{"name": "sleeper", "type": "launch", "affinity": "launch"}],
}

launch_sleep_spoke = {
    "execution": "spoke",
    "portfolio": "DepsRefactor5",
    "product": "sleep5",
    "version": "v1",
    "deploy_to": {"tags": [{"tag": "group:hundred", "regions": "regions_enabled"}]},
    "parameters": {
        "Duration": {"default": "8"},
        "SleeperCustomResourceArn": {
            "ssm": {
                "name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                "path": "/sleeper/SleeperFunctionArn",
            }
        },
    },
    "depends_on": [{"name": "sleeper", "type": "launch", "affinity": "launch"}],
}


@mocker.patch(
    "servicecatalog_puppet.config", new_callable=mocker.MagicMock(name="config")
)
@mocker.patch("builtins.open", new_callable=mocker.MagicMock(name="open"))
def test_generate_complete_task_reference_for_simple_launch(open_mocked, config_mocked):
    # setup
    config_mocked.configure_mock(
        **{"get_home_region.return_value": "eu-west-1",}
    )

    from servicecatalog_puppet.commands import task_reference
    from servicecatalog_puppet import manifest_utils

    f = mocker.MagicMock()
    puppet_account_id = "012345678910"
    manifest = manifest_utils.Manifest(
        dict(
            accounts=[puppet_account, account_from_hundred,],
            launches=dict(sleeper=launch_sleeper,),
        )
    )
    expected_result = {
        "all_tasks": {
            "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-1/launches"
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-1/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-1/launches",
                "param_name": "/sleeper/SleeperFunctionArn/eu-west-1/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-1-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                ],
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-2/launches"
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-2/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-2/launches",
                "param_name": "/sleeper/SleeperFunctionArn/eu-west-2/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-2-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2"
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                ],
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2"
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-3/launches"
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-3/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-3/launches",
                "param_name": "/sleeper/SleeperFunctionArn/eu-west-3/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-3-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3"
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                ],
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3"
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-us-west-1": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-west-1/launches"
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-west-1/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-west-1/launches",
                "param_name": "/sleeper/SleeperFunctionArn/us-west-1/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-us-west-1-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1"
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                ],
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1"
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-us-east-1": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-east-1/launches"
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-east-1/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-east-1/launches",
                "param_name": "/sleeper/SleeperFunctionArn/us-east-1/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-us-east-1-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1"
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                ],
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1"
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
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
    config_mocked.configure_mock(
        **{"get_home_region.return_value": "eu-west-1",}
    )

    from servicecatalog_puppet.commands import task_reference
    from servicecatalog_puppet import manifest_utils

    f = mocker.MagicMock()
    puppet_account_id = "012345678910"
    manifest = manifest_utils.Manifest(
        dict(
            accounts=[puppet_account, account_from_hundred,],
            launches=dict(sleeper=launch_sleeper, sleep=launch_sleep),
        )
    )
    expected_result = {
        "all_tasks": {
            "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-1/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-1/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-1/launches",
                "param_name": "/sleeper/SleeperFunctionArn/eu-west-1/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-1-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-1-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-1-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleep_012345678910-eu-west-1",
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-2/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-2/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-2/launches",
                "param_name": "/sleeper/SleeperFunctionArn/eu-west-2/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-2-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2"
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-2-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-2-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleep_012345678910-eu-west-2",
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-3/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-3/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-3/launches",
                "param_name": "/sleeper/SleeperFunctionArn/eu-west-3/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-3-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3"
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-3-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-3-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleep_012345678910-eu-west-3",
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-us-west-1": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-west-1/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-west-1/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-west-1/launches",
                "param_name": "/sleeper/SleeperFunctionArn/us-west-1/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-us-west-1-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1"
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-west-1-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-us-west-1-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleep_012345678910-us-west-1",
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-us-east-1": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-east-1/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-east-1/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-east-1/launches",
                "param_name": "/sleeper/SleeperFunctionArn/us-east-1/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "hub",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-us-east-1-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1"
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5": {
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-east-1-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-us-east-1-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-eu-west-1": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-eu-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-eu-west-1"
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-eu-west-2": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-eu-west-2",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-eu-west-2"
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-eu-west-3": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-eu-west-3",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-eu-west-3"
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-us-west-1": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-us-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-us-west-1"
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-us-east-1": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-us-east-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-us-east-1"
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn": {
                "account_id": "012345678910",
                "region": "eu-west-1",
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "path": "/sleeper/SleeperFunctionArn",
                "section_name": "ssm_parameters_with_a_path",
                "task_reference": "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                "dependencies_by_reference": [],
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
def test_generate_complete_task_reference_for_launch_with_spoke(
    open_mocked, config_mocked
):
    # setup
    config_mocked.configure_mock(
        **{"get_home_region.return_value": "eu-west-1",}
    )

    from servicecatalog_puppet.commands import task_reference

    f = mocker.MagicMock()
    puppet_account_id = "012345678910"
    new_name = "banana"
    all_tasks = {
        "all_tasks": {
            "launches_sleeper_012345678910-eu-west-1": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-012345678910-eu-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-1/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-1/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-1/launches",
                "param_name": "/sleeper/SleeperFunctionArn/eu-west-1/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "spoke",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-1-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1"
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5": {
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-1-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-1-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleep_012345678910-eu-west-1",
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-2/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-2/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-2/launches",
                "param_name": "/sleeper/SleeperFunctionArn/eu-west-2/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "spoke",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-2-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2"
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5": {
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-2-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-2-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleep_012345678910-eu-west-2",
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-3/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-3/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/eu-west-3/launches",
                "param_name": "/sleeper/SleeperFunctionArn/eu-west-3/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "spoke",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-3-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3"
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5": {
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-3-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-eu-west-3-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleep_012345678910-eu-west-3",
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-us-west-1": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-west-1/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-west-1/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-west-1/launches",
                "param_name": "/sleeper/SleeperFunctionArn/us-west-1/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "spoke",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-us-west-1-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1"
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5": {
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-west-1-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-us-west-1-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleep_012345678910-us-west-1",
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleeper_${AWS::PuppetAccountId}-us-east-1": {
                "launch_name": "sleeper",
                "ssm_param_outputs": [
                    {
                        "param_name": "/sleeper/SleeperFunctionArn/${AWS::Region}/launches",
                        "stack_output": "SleeperFunctionArn",
                    }
                ],
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "execution": "hub",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "section_name": "launches",
                "item_name": "sleeper",
                "dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
                ],
                "reverse_dependencies_by_reference": [
                    "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-east-1/launches",
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "task_reference": "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
            },
            "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-east-1/launches": {
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
                "task_reference": "ssm_outputs-${AWS::PuppetAccountId}-eu-west-1-/sleeper/SleeperFunctionArn/us-east-1/launches",
                "param_name": "/sleeper/SleeperFunctionArn/us-east-1/launches",
                "stack_output": "SleeperFunctionArn",
                "force_operation": False,
                "account_id": "012345678910",
                "region": "eu-west-1",
                "dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1"
                ],
                "reverse_dependencies_by_reference": [],
                "task_generating_output": "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                "status": None,
                "section_name": "ssm_outputs",
            },
            "portfolio-local-012345678910-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-local-012345678910-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [],
                "reverse_dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                    "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1",
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "status": None,
                "execution": "spoke",
                "section_name": "portfolio-local",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "task_reference": "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "portfolio_task_reference": "portfolio-local-012345678910-us-east-1-DepsRefactor5",
                "section_name": "portfolio-share-and-accept-account",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio_share_and_accept-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "sharing_mode": "ACCOUNT",
                "section_name": "portfolio-imported",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5": {
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-puppet-role-association-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "portfolio_task_reference": "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1"
                ],
                "account_id": "${AWS::PuppetAccountId}",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "execution": "hub",
                "section_name": "portfolio-puppet-role-association",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleeper5-v1",
                "dependencies_by_reference": [
                    "portfolio-imported-${AWS::PuppetAccountId}-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1"
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "product": "sleeper5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleeper",
                "manifest_account_id": "${AWS::PuppetAccountId}",
            },
            "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5": {
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "task_reference": "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-east-1-DepsRefactor5"
                ],
                "portfolio_task_reference": "portfolio-local-012345678910-us-east-1-DepsRefactor5",
                "reverse_dependencies_by_reference": [
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "section_name": "portfolio-get-all-products-and-their-versions",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-eu-west-1": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-eu-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-1-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-eu-west-1"
                ],
                "account_id": "012345678910",
                "region": "eu-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-eu-west-2": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-eu-west-2",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-2-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-2-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-2-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-eu-west-2"
                ],
                "account_id": "012345678910",
                "region": "eu-west-2",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-eu-west-3": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-eu-west-3",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-eu-west-3-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-eu-west-3-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-eu-west-3-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-eu-west-3"
                ],
                "account_id": "012345678910",
                "region": "eu-west-3",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-us-west-1": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-us-west-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-west-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-west-1-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-west-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-us-west-1"
                ],
                "account_id": "012345678910",
                "region": "us-west-1",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "launches_sleep_012345678910-us-east-1": {
                "launch_name": "sleep",
                "ssm_param_outputs": [],
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "execution": "spoke",
                "puppet_account_id": "012345678910",
                "status": None,
                "requested_priority": 0,
                "dependencies": [
                    {"name": "sleeper", "type": "launch", "affinity": "launch"}
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "section_name": "launches",
                "item_name": "sleep",
                "dependencies_by_reference": [
                    "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                    "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1",
                    "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-2",
                    "launches_sleeper_${AWS::PuppetAccountId}-eu-west-3",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-west-1",
                    "launches_sleeper_${AWS::PuppetAccountId}-us-east-1",
                ],
                "reverse_dependencies_by_reference": [],
                "task_reference": "launches_sleep_012345678910-us-east-1",
                "portfolio_get_all_products_and_their_versions_ref": "portfolio-get-all-products-and-their-versions-012345678910-us-east-1-DepsRefactor5",
                "describe_provisioning_params_ref": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1",
            },
            "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1": {
                "puppet_account_id": "012345678910",
                "task_reference": "describe-provisioning-parameters-012345678910-us-east-1-DepsRefactor5-sleep5-v1",
                "dependencies_by_reference": [
                    "portfolio-local-012345678910-us-east-1-DepsRefactor5"
                ],
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-us-east-1"
                ],
                "account_id": "012345678910",
                "region": "us-east-1",
                "portfolio": "DepsRefactor5",
                "product": "sleep5",
                "version": "v1",
                "section_name": "describe-provisioning-parameters",
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
            },
            "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn": {
                "account_id": "012345678910",
                "region": "eu-west-1",
                "reverse_dependencies_by_reference": [
                    "launches_sleep_012345678910-eu-west-1",
                    "launches_sleep_012345678910-eu-west-2",
                    "launches_sleep_012345678910-eu-west-3",
                    "launches_sleep_012345678910-us-west-1",
                    "launches_sleep_012345678910-us-east-1",
                ],
                "manifest_section_name": "launches",
                "manifest_item_name": "sleep",
                "manifest_account_id": "012345678910",
                "path": "/sleeper/SleeperFunctionArn",
                "section_name": "ssm_parameters_with_a_path",
                "task_reference": "ssm_parameters_with_a_path-012345678910-eu-west-1-/sleeper/SleeperFunctionArn",
                "dependencies_by_reference": [],
            },
        }
    }
    expected_result = {}

    # exercise
    actual_result = task_reference.generate_hub_task_reference(
        puppet_account_id, all_tasks.get("all_tasks"), new_name,
    )

    # verify
    assert actual_result == expected_result
