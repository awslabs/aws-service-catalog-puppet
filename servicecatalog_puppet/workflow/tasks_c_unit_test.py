# from . import tasks_unit_tests
#
#
# class PuppetTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import tasks
#
#         self.sut = tasks.PuppetTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {"Hello": "World"}
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class GetSSMParamTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import tasks
#
#         self.sut = tasks.GetSSMParamTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "parameter_name": self.parameter_name,
#             "name": self.name,
#             "region": self.region,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
