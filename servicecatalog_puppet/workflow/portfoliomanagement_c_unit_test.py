from . import tasks_unit_tests


class GetVersionIdByVersionNameTest(tasks_unit_tests.PuppetTaskUnitTest):

    puppet_account_id = "01234567890"
    manifest_file_path = "tcvyuiho"
    portfolio = "port1"
    portfolio_id = "psdsdort1"
    product = "prod1"
    product_id = "sdsdprod1"
    version = "v1"
    account_id = "23089479278643892"
    region = "eu-west-1"
    cache_invalidator = "foo"

    def setUp(self) -> None:
        from . import portfoliomanagement

        self.sut = portfoliomanagement.GetVersionIdByVersionName(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            portfolio=self.portfolio,
            portfolio_id=self.portfolio_id,
            product=self.product,
            product_id=self.product_id,
            version=self.version,
            account_id=self.account_id,
            region=self.region,
            cache_invalidator=self.cache_invalidator,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


class SearchProductsAsAdminTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    puppet_account_id = "01234567890"
    manifest_file_path = "tcvyuiho"
    portfolio = "port1"
    portfolio_id = "psdlsdm;lmort1"
    account_id = "23089479278643892"
    region = "eu-west-1"
    cache_invalidator = "foo"

    def setUp(self) -> None:
        from . import portfoliomanagement

        self.sut = portfoliomanagement.SearchProductsAsAdminTask(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            portfolio=self.portfolio,
            portfolio_id=self.portfolio_id,
            account_id=self.account_id,
            region=self.region,
            cache_invalidator=self.cache_invalidator,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


class GetProductIdByProductNameTest(tasks_unit_tests.PuppetTaskUnitTest):
    puppet_account_id = "01234567890"
    manifest_file_path = "tcvyuiho"
    portfolio = "portfolio1"
    portfolio_id = "sdsdsdsdportfolio1"
    product = "prod1"
    account_id = "23089479278643892"
    region = "eu-west-1"
    cache_invalidator = "foo"

    def setUp(self) -> None:
        from . import portfoliomanagement

        self.sut = portfoliomanagement.GetProductIdByProductName(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            portfolio=self.portfolio,
            portfolio_id=self.portfolio_id,
            product=self.product,
            account_id=self.account_id,
            region=self.region,
            cache_invalidator=self.cache_invalidator,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "product": self.product,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())

    def test_requires(self):
        from . import portfoliomanagement

        expected_result = {
            "search_products_as_admin": portfoliomanagement.SearchProductsAsAdminTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                account_id=self.account_id,
                region=self.region,
                cache_invalidator=self.cache_invalidator,
            ),
        }
        self.assertEqual(expected_result, self.sut.requires())


class GetPortfolioByPortfolioNameTest(tasks_unit_tests.PuppetTaskUnitTest):
    puppet_account_id = "01234567890"
    manifest_file_path = "tcvyuiho"
    portfolio = "portfolio1"
    account_id = "23089479278643892"
    region = "eu-west-1"
    cache_invalidator = "foo"

    def setUp(self) -> None:
        from . import portfoliomanagement

        self.sut = portfoliomanagement.GetPortfolioByPortfolioName(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            portfolio=self.portfolio,
            account_id=self.account_id,
            region=self.region,
            cache_invalidator=self.cache_invalidator,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


# class ProvisionActionTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.ProvisionActionTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "type": self.type,
#             "source": self.source,
#             "phase": self.phase,
#             "source_type": self.source_type,
#             "name": self.name,
#             "project_name": self.project_name,
#             "account_id": self.account_id,
#             "region": self.region,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class CreateSpokeLocalPortfolioTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.CreateSpokeLocalPortfolioTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class CreateAssociationsForPortfolioTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.CreateAssociationsForPortfolioTask(
#         )
#
#     def test_requires(self):
#         expected_result = {
#             "create_spoke_local_portfolio_task": CreateSpokeLocalPortfolioTask(
#                 manifest_file_path=self.manifest_file_path,
#                 puppet_account_id=self.puppet_account_id,
#                 account_id=self.account_id,
#                 region=self.region,
#                 portfolio=self.portfolio,
#                 organization=self.organization,
#             ),
#         }
#         self.assertEqual(expected_result, self.sut.requires())
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class GetProductsAndProvisioningArtifactsTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.GetProductsAndProvisioningArtifactsTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "region": self.region,
#             "portfolio": self.portfolio,
#             "puppet_account_id": self.puppet_account_id,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#     def test_requires(self):
#         expected_result = {
#             "search_products_as_admin": SearchProductsAsAdminTask(
#                 manifest_file_path=self.manifest_file_path,
#                 puppet_account_id=self.puppet_account_id,
#                 portfolio=self.portfolio,
#                 region=self.region,
#                 account_id=self.puppet_account_id,
#             )
#         }
#         self.assertEqual(expected_result, self.sut.requires())
#
#
# class CopyIntoSpokeLocalPortfolioTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.CopyIntoSpokeLocalPortfolioTask(
#         )
#
#     def test_requires(self):
#         expected_result = {
#             "create_spoke_local_portfolio": CreateSpokeLocalPortfolioTask(
#                 manifest_file_path=self.manifest_file_path,
#                 account_id=self.account_id,
#                 region=self.region,
#                 portfolio=self.portfolio,
#                 organization=self.organization,
#                 puppet_account_id=self.puppet_account_id,
#             ),
#             "products_and_provisioning_artifacts": GetProductsAndProvisioningArtifactsTask(
#                 manifest_file_path=self.manifest_file_path,
#                 region=self.region,
#                 portfolio=self.portfolio,
#                 puppet_account_id=self.puppet_account_id,
#             ),
#         }
#         self.assertEqual(expected_result, self.sut.requires())
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class ImportIntoSpokeLocalPortfolioTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.ImportIntoSpokeLocalPortfolioTask(
#         )
#
#     def test_requires(self):
#         expected_result = {
#             "create_spoke_local_portfolio": CreateSpokeLocalPortfolioTask(
#                 manifest_file_path=self.manifest_file_path,
#                 puppet_account_id=self.puppet_account_id,
#                 account_id=self.account_id,
#                 region=self.region,
#                 portfolio=self.portfolio,
#                 organization=self.organization,
#             ),
#             "products_and_provisioning_artifacts": GetProductsAndProvisioningArtifactsTask(
#                 manifest_file_path=self.manifest_file_path,
#                 region=self.region,
#                 portfolio=self.portfolio,
#                 puppet_account_id=self.puppet_account_id,
#             ),
#             "hub_portfolio": GetPortfolioByPortfolioName(
#                 manifest_file_path=self.manifest_file_path,
#                 puppet_account_id=self.puppet_account_id,
#                 portfolio=self.portfolio,
#                 account_id=self.puppet_account_id,
#                 region=self.region,
#             ),
#         }
#         self.assertEqual(expected_result, self.sut.requires())
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class CreateLaunchRoleConstraintsForPortfolioTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.CreateLaunchRoleConstraintsForPortfolio(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class SharePortfolioTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.SharePortfolioTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class ShareAndAcceptPortfolioTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.ShareAndAcceptPortfolioTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#             "puppet_account_id": self.puppet_account_id,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class CreateAssociationsInPythonForPortfolioTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.CreateAssociationsInPythonForPortfolioTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#     def test_api_calls_used(self):
#         expected_result = {
#             f"servicecatalog.associate_principal_with_portfolio_{self.region}": 1,
#         }
#         self.assertEqual(expected_result, self.sut.api_calls_used())
#
#
# class CreateShareForAccountLaunchRegionTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.CreateShareForAccountLaunchRegion(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class DisassociateProductFromPortfolioTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.DisassociateProductFromPortfolio(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio_id": self.portfolio_id,
#             "product_id": self.product_id,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#     def test_api_calls_used(self):
#         expected_result = {
#             f"servicecatalog.disassociate_product_from_portfolio_{self.account_id}_{self.region}_{self.portfolio_id}_{self.product_id}": 1,
#         }
#         self.assertEqual(expected_result, self.sut.api_calls_used())
#
#
# class DisassociateProductsFromPortfolioTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.DisassociateProductsFromPortfolio(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio_id": self.portfolio_id,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#     def test_api_calls_used(self):
#         expected_result = {
#             f"servicecatalog.search_products_as_admin_single_page_{self.account_id}_{self.region}_{self.portfolio_id}": 1,
#         }
#         self.assertEqual(expected_result, self.sut.api_calls_used())
#
#
# class DeleteLocalPortfolioTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.DeleteLocalPortfolio(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio_id": self.portfolio_id,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#     def test_api_calls_used(self):
#         expected_result = {
#             f"servicecatalog.delete_portfolio_{self.account_id}_{self.region}_{self.portfolio_id}": 1,
#         }
#         self.assertEqual(expected_result, self.sut.api_calls_used())
#
#
# class DeletePortfolioShareTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.DeletePortfolioShare(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#     def test_api_calls_used(self):
#         expected_result = {
#             f"servicecatalog.list_accepted_portfolio_shares_{self.account_id}_{self.region}_{self.portfolio}": 1,
#             f"servicecatalog.delete_portfolio_share_{self.puppet_account_id}_{self.region}_{self.portfolio}": 1,
#         }
#         self.assertEqual(expected_result, self.sut.api_calls_used())
#
#
# class DeletePortfolioTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import portfoliomanagement
#
#         self.sut = portfoliomanagement.DeletePortfolio(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "account_id": self.account_id,
#             "region": self.region,
#             "portfolio": self.portfolio,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
