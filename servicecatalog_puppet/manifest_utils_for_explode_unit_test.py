#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import unittest
from copy import deepcopy

from servicecatalog_puppet import constants


class TestManifestForExplode(unittest.TestCase):
    account_a = {
        "account_id": "012345678910",
        "default_region": "eu-west-1",
        "name": "accounta",
        "expanded_from": "ou-aaaa-aaaaaaaa",
        "organization": "o-aaaaaaaa",
        "regions_enabled": ["eu-west-2",],
        "tags": ["group:A"],
    }
    account_b = {
        "account_id": "009876543210",
        "default_region": "us-west-1",
        "expanded_from": "ou-bbbb-bbbbbbbb",
        "organization": "o-bbbbbbbb",
        "name": "accountb",
        "regions_enabled": ["us-west-2",],
        "tags": ["group:B"],
    }
    account_c = {
        "account_id": "432100098765",
        "default_region": "ap-west-1",
        "name": "accountc",
        "regions_enabled": ["ap-west-2",],
        "tags": ["group:C"],
    }
    accounts = [
        account_a,
        account_b,
        account_c,
    ]

    lambda_invocation_with_no_dependencies = dict(
        product="lambda_invocation_with_no_dependencies",
    )
    lambda_invocation_with_one_lambda_dependency = dict(
        function_name="lambda_invocation_with_one_lambda_dependency",
        depends_on=[
            dict(
                name="lambda_invocation_with_no_dependencies",
                type=constants.LAMBDA_INVOCATION,
            )
        ],
    )
    lambda_invocation_with_one_launch_dependency = dict(
        function_name="lambda_invocation_with_one_launch_dependency",
        depends_on=[dict(name="launch_with_no_dependencies", type=constants.LAUNCH,)],
    )
    launch_with_no_dependencies = dict(product="launch_with_no_dependencies",)
    spoke_local_portfolio_with_no_dependencies = dict(
        product="spoke_local_portfolio_with_no_dependencies",
    )
    spoke_local_portfolio_with_one_launch_dependency = dict(
        product="spoke_local_portfolio_with_one_launch_dependency",
        depends_on=["launch_with_no_dependencies"],
    )
    launch_depending_on_depending_launch = dict(
        product="launch_depending_on_depending_launch",
        depends_on=[dict(type=constants.LAUNCH, name="launch_depending_on_launch")],
    )
    launch_depending_on_launch = dict(
        product="launch_depending_on_launch",
        depends_on=[dict(type=constants.LAUNCH, name="launch_with_no_dependencies")],
    )
    another_launch_with_no_dependencies = dict(
        product="another_launch_with_no_dependencies",
    )
    launch_with_one_lambda_dependency = dict(
        function_name="launch_with_one_lambda_dependency",
        depends_on=["launch_with_no_dependencies"],
    )
    launch_depending_on_lambda = dict(
        function_name="launch_depending_on_lambda",
        depends_on=[
            dict(
                name="lambda_invocation_with_no_dependencies",
                type=constants.LAMBDA_INVOCATION,
            )
        ],
    )

    def setUp(self):
        self.maxDiff = None
        from servicecatalog_puppet import manifest_utils

        self.sut = manifest_utils.explode

    def tearDown(self):
        self.sut = None

    def test_explode_simple_for_lambda_invoke(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(
                lambda_invocation_with_no_dependencies=self.lambda_invocation_with_no_dependencies
            ),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_simple_for_launch(self):
        # setup

        expanded_manifest = {
            constants.LAUNCHES: dict(
                launch_with_no_dependencies=self.launch_with_no_dependencies
            ),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_simple_for_spoke_local_portfolio(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(
                spoke_local_portfolio_with_no_dependencies=self.spoke_local_portfolio_with_no_dependencies
            ),
            constants.LAMBDA_INVOCATIONS: dict(),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_simple_for_spoke_local_portfolio_depends_on_launch(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(
                launch_with_no_dependencies=self.launch_with_no_dependencies,
            ),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(
                spoke_local_portfolio_with_no_dependencies=self.spoke_local_portfolio_with_one_launch_dependency,
            ),
            constants.LAMBDA_INVOCATIONS: dict(),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_simple_for_two_launches(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(
                launch_with_no_dependencies=self.launch_with_no_dependencies,
                another_launch_with_no_dependencies=self.another_launch_with_no_dependencies,
            ),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results_1 = deepcopy(expanded_manifest)
        expected_results_1[constants.LAUNCHES] = dict(
            launch_with_no_dependencies=self.launch_with_no_dependencies,
        )
        expected_results_2 = deepcopy(expanded_manifest)
        expected_results_2[constants.LAUNCHES] = dict(
            another_launch_with_no_dependencies=self.another_launch_with_no_dependencies,
        )
        expected_results = [expected_results_1, expected_results_2]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_single_lambda_dependency_on_lambda(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(
                lambda_invocation_with_no_dependencies=self.lambda_invocation_with_no_dependencies,
                lambda_invocation_with_one_lambda_dependency=self.lambda_invocation_with_one_lambda_dependency,
            ),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_single_lambda_dependency_on_launch(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(
                launch_with_no_dependencies=self.launch_with_no_dependencies
            ),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(
                lambda_invocation_with_one_launch_dependency=self.lambda_invocation_with_one_launch_dependency,
            ),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_single_launch_depends_on_lambda(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(
                launch_depending_on_lambda=self.launch_depending_on_lambda
            ),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(
                lambda_invocation_with_no_dependencies=self.lambda_invocation_with_no_dependencies,
            ),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_single_lambda_dependency_on_lambda_reversed(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(
                lambda_invocation_with_one_lambda_dependency=self.lambda_invocation_with_one_lambda_dependency,
                lambda_invocation_with_no_dependencies=self.lambda_invocation_with_no_dependencies,
            ),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_single_launch_dependency_on_launch(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(
                launch_with_no_dependencies=self.launch_with_no_dependencies,
                launch_with_one_lambda_dependency=self.launch_with_one_lambda_dependency,
            ),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_single_launch_dependency_on_launch_reversed(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(
                launch_with_one_lambda_dependency=self.launch_with_one_lambda_dependency,
                launch_with_no_dependencies=self.launch_with_no_dependencies,
            ),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)

    def test_explode_3_launches_with_a_gap(self):
        # setup
        expanded_manifest = {
            constants.LAUNCHES: dict(
                launch_depending_on_depending_launch=self.launch_depending_on_depending_launch,
                launch_with_no_dependencies=self.launch_with_no_dependencies,
                launch_depending_on_launch=self.launch_depending_on_launch,
            ),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.LAMBDA_INVOCATIONS: dict(),
            constants.ASSERTIONS: dict(),
            constants.SERVICE_CONTROL_POLICIES: dict(),
            constants.TAG_POLICIES: dict(),
            constants.APPS: dict(),
            constants.WORKSPACES: dict(),
        }

        expected_results = [expanded_manifest]

        # exercise
        actual_results = self.sut(expanded_manifest)

        # verify
        self.assertListEqual(actual_results, expected_results)
