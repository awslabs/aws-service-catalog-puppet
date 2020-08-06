# from . import tasks_unit_tests
#
#
# class SpokeLocalPortfolioSectionTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import spoke_local_portfolios
#
#         self.sut = spoke_local_portfolios.SpokeLocalPortfolioSectionTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "puppet_account_id": self.puppet_account_id,
#             "manifest_file_path": self.manifest_file_path,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
