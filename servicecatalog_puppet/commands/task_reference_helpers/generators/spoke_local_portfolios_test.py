#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import unittest

from servicecatalog_puppet import constants, task_reference_constants


class ImportedPortfoliosTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        from servicecatalog_puppet.commands.task_reference_helpers.generators import (
            spoke_local_portfolios,
        )

        self.sut = spoke_local_portfolios

    def test_for_accounts(self):
        # setup
        puppet_account_id = "hub_account_id"
        account_id = "spoke_account_id"
        region = "eu-west-0"
        item_name = "depsrefactor"
        portfolio = "DepsRefactor"

        section_name = constants.IMPORTED_PORTFOLIOS
        task_to_add = {
            "spoke_local_portfolio_name": item_name,
            "execution": "hub",
            "sharing_mode": "AWS_ORGANIZATIONS",
            "share_tag_options": "True",
            "share_principals": "True",
            "associations": ["arn:aws:iam::${AWS::AccountId}:role/Admin"],
            "portfolio": portfolio,
            "puppet_account_id": puppet_account_id,
            "status": None,
            "requested_priority": 0,
            "dependencies": [],
            "account_id": account_id,
            "organization": "o-sw3edla4pd",
            "ou": "ou-do8d-me7f39on",
            "region": region,
            task_reference_constants.MANIFEST_SECTION_NAMES: {
                "imported-portfolios": True
            },
            task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
            task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
            "section_name": section_name,
            "item_name": item_name,
            "dependencies_by_reference": ["create-policies"],
            "task_reference": f"imported-portfolios_{item_name}_{account_id}_{region}",
            "resources_required": [
                f"SERVICE_CATALOG_LIST_PORTFOLIOS_{region}_OF_{account_id}",
                f"SERVICE_CATALOG_CREATE_PORTFOLIOS_{region}_OF_{account_id}",
            ],
        }
        all_tasks_task_reference = task_to_add["task_reference"]
        all_tasks = {all_tasks_task_reference: task_to_add}
        task_reference = f"{account_id}-{region}"

        # exercise
        self.sut.handle_spoke_local_portfolios(
            all_tasks,
            all_tasks_task_reference,
            item_name,
            puppet_account_id,
            section_name,
            task_reference,
            task_to_add,
        )

        # verify
        n_all_tasks = len(all_tasks.keys())
        self.assertEqual(task_to_add, all_tasks[all_tasks_task_reference])
        self.assertEqual(
            {
                "account_id": puppet_account_id,
                "dependencies_by_reference": [],
                "execution": "hub",
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "portfolio": portfolio,
                "puppet_account_id": puppet_account_id,
                "region": region,
                "section_name": constants.PORTFOLIO_LOCAL,
                "status": None,
                "task_reference": f"portfolio-local-{puppet_account_id}-{region}-{portfolio}",
            },
            all_tasks[f"portfolio-local-{puppet_account_id}-{region}-{portfolio}"],
        )

        self.assertEqual(
            {
                "account_id": puppet_account_id,
                "dependencies_by_reference": [
                    f"portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                    "create-policies",
                ],
                "execution": "hub",
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "portfolio": portfolio,
                "portfolio_task_reference": f"portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                "puppet_account_id": puppet_account_id,
                "region": region,
                "section_name": "portfolio-puppet-role-association",
                "task_reference": f"portfolio-puppet-role-association-{puppet_account_id}-{region}-{portfolio}",
            },
            all_tasks[
                f"portfolio-puppet-role-association-{puppet_account_id}-{region}-{portfolio}"
            ],
        )

        self.assertEqual(
            {
                "account_id": puppet_account_id,
                "dependencies_by_reference": [
                    f"portfolio-local-{puppet_account_id}-{region}-{portfolio}"
                ],
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "portfolio_task_reference": f"portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                "region": region,
                "section_name": "describe-portfolio-shares",
                "task_reference": f"describe-portfolio-shares-ORGANIZATIONAL_UNIT-portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                "type": "ORGANIZATIONAL_UNIT",
            },
            all_tasks[
                f"describe-portfolio-shares-ORGANIZATIONAL_UNIT-portfolio-local-{puppet_account_id}-{region}-{portfolio}"
            ],
        )

        self.assertEqual(
            {
                "account_id": account_id,
                "dependencies_by_reference": [
                    f"portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                    "create-policies",
                    f"describe-portfolio-shares-ORGANIZATIONAL_UNIT-portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                ],
                "describe_portfolio_shares_task_ref": f"describe-portfolio-shares-ORGANIZATIONAL_UNIT-portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                "execution": "hub",
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "ou_to_share_with": "ou-do8d-me7f39on",
                "portfolio": portfolio,
                "portfolio_task_reference": f"portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                "puppet_account_id": puppet_account_id,
                "region": region,
                "section_name": "portfolio-share-and-accept-aws_organizations",
                "share_principals": "True",
                "share_tag_options": "True",
                "task_reference": f"portfolio_share_and_accept-ou-do8d-me7f39on-{region}-{portfolio}",
            },
            all_tasks[
                f"portfolio_share_and_accept-ou-do8d-me7f39on-{region}-{portfolio}"
            ],
        )

        self.assertEqual(
            {
                "account_id": puppet_account_id,
                "dependencies_by_reference": [
                    f"portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                    f"portfolio-puppet-role-association-{puppet_account_id}-{region}-{portfolio}",
                ],
                "execution": "hub",
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "portfolio_task_reference": f"portfolio-local-{puppet_account_id}-{region}-{portfolio}",
                "puppet_account_id": puppet_account_id,
                "region": region,
                "section_name": "portfolio-get-all-products-and-their-versions",
                "task_reference": f"portfolio-get-all-products-and-their-versions-before-{puppet_account_id}-{region}-{portfolio}",
            },
            all_tasks[
                f"portfolio-get-all-products-and-their-versions-before-{puppet_account_id}-{region}-{portfolio}"
            ],
        )

        self.assertEqual(
            {
                "account_id": account_id,
                "dependencies_by_reference": [
                    f"imported-portfolios_{item_name}_{account_id}_{region}",
                    "create-policies",
                ],
                "execution": "hub",
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "portfolio": portfolio,
                "portfolio_task_reference": f"imported-portfolios_{item_name}_{account_id}_{region}",
                "puppet_account_id": puppet_account_id,
                "region": region,
                "section_name": "portfolio-puppet-role-association",
                "task_reference": f"portfolio-puppet-role-association-{account_id}-{region}-{portfolio}",
            },
            all_tasks[
                f"portfolio-puppet-role-association-{account_id}-{region}-{portfolio}"
            ],
        )

        self.assertEqual(
            {
                "account_id": account_id,
                "dependencies_by_reference": [
                    f"imported-portfolios_{item_name}_{account_id}_{region}",
                    f"portfolio-puppet-role-association-{account_id}-{region}-{portfolio}",
                ],
                "execution": "hub",
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "portfolio": portfolio,
                "portfolio_task_reference": f"imported-portfolios_{item_name}_{account_id}_{region}",
                "region": region,
                "section_name": "portfolio-get-all-products-and-their-versions",
                "status": None,
                "task_reference": f"portfolio-get-all-products-and-their-versions-{account_id}-{region}-{portfolio}",
            },
            all_tasks[
                f"portfolio-get-all-products-and-their-versions-{account_id}-{region}-{portfolio}"
            ],
        )

        self.assertEqual(
            {
                "account_id": account_id,
                "dependencies_by_reference": [
                    f"imported-portfolios_{item_name}_{account_id}_{region}",
                    f"portfolio-get-all-products-and-their-versions-{account_id}-{region}-{portfolio}",
                    f"portfolio-get-all-products-and-their-versions-before-{puppet_account_id}-{region}-{portfolio}",
                ],
                "execution": "hub",
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "portfolio": portfolio,
                "portfolio_get_all_products_and_their_versions_for_hub_ref": f"portfolio-get-all-products-and-their-versions-before-{puppet_account_id}-{region}-{portfolio}",
                "portfolio_get_all_products_and_their_versions_ref": f"portfolio-get-all-products-and-their-versions-{account_id}-{region}-{portfolio}",
                "portfolio_task_reference": f"imported-portfolios_{item_name}_{account_id}_{region}",
                "product_generation_mathod": None,
                "region": region,
                "section_name": "portfolio-None",
                "status": None,
                "task_reference": f"portfolio_None-imported-portfolios-{item_name}-{account_id}-{region}-{portfolio}",
            },
            all_tasks[
                f"portfolio_None-imported-portfolios-{item_name}-{account_id}-{region}-{portfolio}"
            ],
        )

        self.assertEqual(
            {
                "account_id": account_id,
                "associations": ["arn:aws:iam::${AWS::AccountId}:role/Admin"],
                "dependencies_by_reference": [
                    f"imported-portfolios_{item_name}_{account_id}_{region}",
                    "create-policies",
                ],
                "execution": "hub",
                "spoke_local_portfolio_name": item_name,
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "portfolio": portfolio,
                "portfolio_task_reference": f"imported-portfolios_{item_name}_{account_id}_{region}",
                "region": region,
                "section_name": "portfolio-associations",
                "status": None,
                "task_reference": f"portfolio_associations-imported-portfolios-{item_name}-{account_id}-{region}",
            },
            all_tasks[
                f"portfolio_associations-imported-portfolios-{item_name}-{account_id}-{region}"
            ],
        )

        self.assertEqual(
            {
                "account_id": account_id,
                "dependencies_by_reference": [
                    f"imported-portfolios_{item_name}_{account_id}_{region}",
                    f"portfolio-puppet-role-association-{account_id}-{region}-{portfolio}",
                    f"portfolio_None-imported-portfolios-{item_name}-{account_id}-{region}-{portfolio}",
                ],
                "execution": "hub",
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    "imported-portfolios": True
                },
                "portfolio": portfolio,
                "portfolio_task_reference": f"imported-portfolios_{item_name}_{account_id}_{region}",
                "region": region,
                "section_name": f"portfolio-get-all-products-and-their-versions",
                "status": None,
                "task_reference": f"portfolio-get-all-products-and-their-versions-after-{account_id}-{region}-{portfolio}",
            },
            all_tasks[
                f"portfolio-get-all-products-and-their-versions-after-{account_id}-{region}-{portfolio}"
            ],
        )
        self.assertEqual(11, n_all_tasks)
