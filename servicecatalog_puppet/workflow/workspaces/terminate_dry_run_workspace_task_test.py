from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class TerminateDryRunWorkspaceTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    workspace_name = "workspace_name"
    region = "region"
    account_id = "account_id"
    bucket = "bucket"
    key = "key"
    version_id = "version_id"
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    ssm_param_outputs = []
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.workspaces import (
            terminate_dry_run_workspace_task,
        )

        self.module = terminate_dry_run_workspace_task

        self.sut = self.module.TerminateDryRunWorkspaceTask(
            **self.get_common_args(),
            workspace_name=self.workspace_name,
            region=self.region,
            account_id=self.account_id,
            bucket=self.bucket,
            key=self.key,
            version_id=self.version_id,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            ssm_param_outputs=self.ssm_param_outputs,
            execution=self.execution
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "workspace_name": self.workspace_name,
            "region": self.region,
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
