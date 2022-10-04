from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class RunDeployInSpokeTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    task_reference = "task_reference"
    dependencies_by_reference = []
    account_id = "account_id"
    generate_manifest_ref = "generate_manifest_ref"

    def setUp(self) -> None:
        import os
        from servicecatalog_puppet import environmental_variables

        os.environ[environmental_variables.REGIONS] = "[]"
        from servicecatalog_puppet.workflow.launch import run_deploy_in_spoke_task

        self.module = run_deploy_in_spoke_task

        self.sut = self.module.RunDeployInSpokeTask(
            **self.get_common_args(),
            account_id=self.account_id,
            generate_manifest_ref=self.generate_manifest_ref,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
