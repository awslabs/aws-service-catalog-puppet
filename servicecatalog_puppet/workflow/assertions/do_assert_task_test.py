from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoAssertTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    assertion_name = "assertion_name"
    region = "region"
    account_id = "account_id"
    execution = "execution"
    expected = {}
    actual = {}
    requested_priority = 1

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.assertions import do_assert_task

        self.module = do_assert_task

        self.sut = self.module.DoAssertTask(
            **self.get_common_args(),
            assertion_name=self.assertion_name,
            region=self.region,
            account_id=self.account_id,
            execution=self.execution,
            expected=self.expected,
            actual=self.actual,
            requested_priority=self.requested_priority,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
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
