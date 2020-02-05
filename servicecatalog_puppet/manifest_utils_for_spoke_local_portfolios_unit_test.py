# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import pytest
import yaml
from pytest import fixture
import json


@fixture
def sut():
    from servicecatalog_puppet import manifest_utils_for_spoke_local_portfolios
    return manifest_utils_for_spoke_local_portfolios


def test_generate_spoke_local_portfolios_tasks_for_spoke_local_portfolio_shared_by_tag(sut, shared_datadir):
    # setup
    manifest = yaml.safe_load(
        (shared_datadir / 'manifest_utils_for_spoke_local_portfolios' / 'simple.yaml').read_text()
    )
    spoke_local_portfolio_name = 'shared_by_tag'
    puppet_account_id = "01234567890"
    should_use_sns = False
    should_use_product_plans = False
    include_expanded_from = False
    single_account = None
    is_dry_run = False

    expected_result = {
        'post_actions': [],
        'pre_actions': [],
        'task_defs': [
            {
                'account_id': '105463962595',
                'associations': [],
                'constraints': {},
                'depends_on': [],
                'expanded_from': '',
                'is_dry_run': False,
                'organization': '',
                'portfolio': 'k-mandatory',
                'puppet_account_id': '01234567890',
                'region': 'eu-west-1',
                'requested_priority': 0,
                'retry_count': 1,
                'should_use_product_plans': False,
                'should_use_sns': False,
                'single_account': None,
                'spoke_local_portfolio_name': 'shared_by_tag',
                'worker_timeout': 0
            },
            {
                'account_id': '105463962595',
                'associations': [],
                'constraints': {},
                'depends_on': [],
                'expanded_from': '',
                'is_dry_run': False,
                'organization': '',
                'portfolio': 'k-mandatory',
                'puppet_account_id': '01234567890',
                'region': 'eu-west-2',
                'requested_priority': 0,
                'retry_count': 1,
                'should_use_product_plans': False,
                'should_use_sns': False,
                'single_account': None,
                'spoke_local_portfolio_name': 'shared_by_tag',
                'worker_timeout': 0
            },
            {
                'account_id': '105463962595',
                'associations': [],
                'constraints': {},
                'depends_on': [],
                'expanded_from': '',
                'is_dry_run': False,
                'organization': '',
                'portfolio': 'k-mandatory',
                'puppet_account_id': '01234567890',
                'region': 'eu-west-3',
                'requested_priority': 0,
                'retry_count': 1,
                'should_use_product_plans': False,
                'should_use_sns': False,
                'single_account': None,
                'spoke_local_portfolio_name': 'shared_by_tag',
                'worker_timeout': 0
            }
        ],
    }

    # execute
    actual_result = sut.generate_spoke_local_portfolios_tasks_for_spoke_local_portfolio(
        spoke_local_portfolio_name, manifest, puppet_account_id, should_use_sns, should_use_product_plans,
        include_expanded_from, single_account, is_dry_run,
    )

    # verify
    assert actual_result == expected_result
