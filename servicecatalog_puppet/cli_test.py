# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pytest import fixture


@fixture
def all_tasks():
    return {
        "012345678910-eu-west-1-all-enable-config": {
            "launch_name": "all-enable-config",
            "portfolio": "ccoe-mandatory-product-portfolio",
            "product": "Config-Enable",
            "version": "v1",
            "product_id": "prod-bbbbbbbbbbb",
            "version_id": "pa-bbbbbbbbbbb",
            "account_id": "012345678910",
            "region": "eu-west-1",
            "puppet_account_id": "012345678911",
            "parameters": [],
            "ssm_param_inputs": [],
            "depends_on": [],
            "dependencies": []
        },
        "012345678910-eu-west-1-all-rules-config": {
            "launch_name": "all-rules-config",
            "portfolio": "ccoe-mandatory-product-portfolio",
            "product": "Config-Rules",
            "version": "v1",
            "product_id": "prod-ccccccccccccc",
            "version_id": "pa-ccccccccccccc",
            "account_id": "012345678910",
            "region": "eu-west-1",
            "puppet_account_id": "012345678911",
            "parameters": [],
            "ssm_param_inputs": [],
            "depends_on": [
                "all-enable-config"
            ],
            "dependencies": []
        },
        "012345678912-eu-west-1-all-enable-config": {
            "launch_name": "all-enable-config",
            "portfolio": "ccoe-mandatory-product-portfolio",
            "product": "Config-Enable",
            "version": "v1",
            "product_id": "prod-bbbbbbbbbbb",
            "version_id": "pa-bbbbbbbbbbb",
            "account_id": "012345678912",
            "region": "eu-west-1",
            "puppet_account_id": "012345678911",
            "parameters": [],
            "ssm_param_inputs": [],
            "depends_on": [],
            "dependencies": []
        },
    }


@fixture
def sut():
    from servicecatalog_puppet import cli
    return cli


def test_wire_dependencies(sut, all_tasks):
    # setup
    expected_result = [
        {
            "launch_name": "all-enable-config",
            "portfolio": "ccoe-mandatory-product-portfolio",
            "product": "Config-Enable",
            "version": "v1",
            "product_id": "prod-bbbbbbbbbbb",
            "version_id": "pa-bbbbbbbbbbb",
            "account_id": "012345678910",
            "region": "eu-west-1",
            "puppet_account_id": "012345678911",
            "parameters": [],
            "ssm_param_inputs": [],
            "dependencies": []
        },
        {
            "launch_name": "all-rules-config",
            "portfolio": "ccoe-mandatory-product-portfolio",
            "product": "Config-Rules",
            "version": "v1",
            "product_id": "prod-ccccccccccccc",
            "version_id": "pa-ccccccccccccc",
            "account_id": "012345678910",
            "region": "eu-west-1",
            "puppet_account_id": "012345678911",
            "parameters": [],
            "ssm_param_inputs": [],
            "dependencies": [
                {
                    "launch_name": "all-enable-config",
                    "portfolio": "ccoe-mandatory-product-portfolio",
                    "product": "Config-Enable",
                    "version": "v1",
                    "product_id": "prod-bbbbbbbbbbb",
                    "version_id": "pa-bbbbbbbbbbb",
                    "account_id": "012345678910",
                    "region": "eu-west-1",
                    "puppet_account_id": "012345678911",
                    "parameters": [],
                    "ssm_param_inputs": [],
                    "dependencies": []
                },
                {
                    "launch_name": "all-enable-config",
                    "portfolio": "ccoe-mandatory-product-portfolio",
                    "product": "Config-Enable",
                    "version": "v1",
                    "product_id": "prod-bbbbbbbbbbb",
                    "version_id": "pa-bbbbbbbbbbb",
                    "account_id": "012345678912",
                    "region": "eu-west-1",
                    "puppet_account_id": "012345678911",
                    "parameters": [],
                    "ssm_param_inputs": [],
                    "dependencies": []
                },
            ]
        },
        {
            "launch_name": "all-enable-config",
            "portfolio": "ccoe-mandatory-product-portfolio",
            "product": "Config-Enable",
            "version": "v1",
            "product_id": "prod-bbbbbbbbbbb",
            "version_id": "pa-bbbbbbbbbbb",
            "account_id": "012345678912",
            "region": "eu-west-1",
            "puppet_account_id": "012345678911",
            "parameters": [],
            "ssm_param_inputs": [],
            "dependencies": []
        }
    ]

    # exercise
    actual_result = sut.wire_dependencies(all_tasks)

    # verify
    assert expected_result[0] == actual_result[0]
    e = expected_result[1]
    a = actual_result[1]
    assert e == a
    assert expected_result[2] == actual_result[2]
