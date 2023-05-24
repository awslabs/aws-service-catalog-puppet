#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import unittest

from servicecatalog_puppet.waluigi.constants import (
    BLOCKED,
    COMPLETED,
    ERRORED,
    IN_PROGRESS,
    NOT_SET,
    QUEUE_STATUS,
)

from servicecatalog_puppet import constants


task_to_run_reference = "task_to_run"
dependency_task_reference = "dependency"
non_related_task_reference = "non-related"


class TestTaskTopologicalGenerationsWithoutScheduler(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        from servicecatalog_puppet.waluigi.shared_tasks import (
            task_topological_generations_without_scheduler,
        )

        self.sut = task_topological_generations_without_scheduler

    def generate_for_no_dependencies(self):
        task_to_run = dict(
            task_reference=task_to_run_reference, dependencies_by_reference=[]
        )
        all_tasks = dict()
        all_tasks[task_to_run_reference] = task_to_run

        return task_to_run, all_tasks, list(all_tasks.keys())

    def test_has_dependencies_remaining_with_no_dependencies(self):
        # setup
        task_to_run, all_tasks, _ = self.generate_for_no_dependencies()

        expected_is_currently_blocked = False
        expected_is_permanently_blocked = False

        # exercise
        (
            actual_is_currently_blocked,
            actual_is_permanently_blocked,
        ) = self.sut.has_dependencies_remaining(task_to_run, all_tasks)

        # verify
        self.assertEqual(expected_is_currently_blocked, actual_is_currently_blocked)
        self.assertEqual(expected_is_permanently_blocked, actual_is_permanently_blocked)

    def test_get_next_task_to_run_with_no_dependencies(self):
        # setup
        _, all_tasks, tasks_to_run = self.generate_for_no_dependencies()
        resources = dict()

        expected_next_task = all_tasks[task_to_run_reference]
        expected_should_shut_down = False

        # exercise
        actual_next_task, actual_should_shut_down = self.sut.get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )

        # verify
        self.assertEqual(expected_next_task, actual_next_task)
        self.assertEqual(expected_should_shut_down, actual_should_shut_down)

    def test_get_next_task_to_run_with_no_dependencies_and_task_complete(self):
        # setup
        _, all_tasks, tasks_to_run = self.generate_for_no_dependencies()
        resources = dict()
        all_tasks[task_to_run_reference][QUEUE_STATUS] = COMPLETED
        expected_next_task = None
        expected_should_shut_down = True

        # exercise
        actual_next_task, actual_should_shut_down = self.sut.get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )

        # verify
        self.assertEqual(expected_next_task, actual_next_task)
        self.assertEqual(expected_should_shut_down, actual_should_shut_down)

    def generate_has_dependencies_remaining_with_completed_dependencies(self):
        dependency_task = dict(
            task_reference=dependency_task_reference,
            dependencies_by_reference=[],
            QUEUE_STATUS=COMPLETED,
        )
        task_to_run = dict(
            task_reference=task_to_run_reference,
            dependencies_by_reference=[dependency_task_reference],
        )
        all_tasks = dict()
        all_tasks[task_to_run_reference] = task_to_run
        all_tasks[dependency_task_reference] = dependency_task

        return task_to_run, all_tasks, list(all_tasks.keys())

    def test_has_dependencies_remaining_with_completed_dependencies(self):
        # setup
        (
            task_to_run,
            all_tasks,
            _,
        ) = self.generate_has_dependencies_remaining_with_completed_dependencies()

        expected_is_currently_blocked = False
        expected_is_permanently_blocked = False

        # exercise
        (
            actual_is_currently_blocked,
            actual_is_permanently_blocked,
        ) = self.sut.has_dependencies_remaining(task_to_run, all_tasks)

        # verify
        self.assertEqual(expected_is_currently_blocked, actual_is_currently_blocked)
        self.assertEqual(expected_is_permanently_blocked, actual_is_permanently_blocked)

    def test_get_next_task_to_run_with_completed_dependencies(self):
        # setup
        (
            _,
            all_tasks,
            tasks_to_run,
        ) = self.generate_has_dependencies_remaining_with_completed_dependencies()

        resources = dict()
        expected_next_task_reference = all_tasks[task_to_run_reference]
        expected_should_shutdown = False

        # exercise
        actual_next_task, actual_should_shutdown = self.sut.get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )

        # verify
        self.assertEqual(expected_next_task_reference, actual_next_task)
        self.assertEqual(expected_should_shutdown, actual_should_shutdown)

    def generate_has_dependencies_remaining_with_not_set_dependencies(self):
        dependency_task = dict(
            task_reference=dependency_task_reference,
            dependencies_by_reference=[],
            QUEUE_STATUS=NOT_SET,
        )
        task_to_run = dict(
            task_reference=task_to_run_reference,
            dependencies_by_reference=[dependency_task_reference],
        )
        all_tasks = dict()
        all_tasks[task_to_run_reference] = task_to_run
        all_tasks[dependency_task_reference] = dependency_task

        return task_to_run, all_tasks, list(all_tasks.keys())

    def test_has_dependencies_remaining_with_not_set_dependencies(self):
        # setup
        (
            task_to_run,
            all_tasks,
            _,
        ) = self.generate_has_dependencies_remaining_with_not_set_dependencies()

        expected_is_currently_blocked = True
        expected_is_permanently_blocked = False

        # exercise
        (
            actual_is_currently_blocked,
            actual_is_permanently_blocked,
        ) = self.sut.has_dependencies_remaining(task_to_run, all_tasks)

        # verify
        self.assertEqual(expected_is_currently_blocked, actual_is_currently_blocked)
        self.assertEqual(expected_is_permanently_blocked, actual_is_permanently_blocked)

    def test_get_next_task_to_run_remaining_with_not_set_dependencies(self):
        # setup
        (
            _,
            all_tasks,
            tasks_to_run,
        ) = self.generate_has_dependencies_remaining_with_not_set_dependencies()

        resources = dict()
        expected_next_task = all_tasks[dependency_task_reference]
        expected_should_shut_down = False

        # exercise
        (actual_next_task, actual_should_shut_down,) = self.sut.get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )

        # verify
        self.assertEqual(expected_next_task, actual_next_task)
        self.assertEqual(expected_should_shut_down, actual_should_shut_down)

    def generate_has_dependencies_remaining_with_failed_dependencies(self):
        dependency_task = dict(
            task_reference=dependency_task_reference,
            dependencies_by_reference=[],
            QUEUE_STATUS=ERRORED,
        )
        task_to_run = dict(
            task_reference=task_to_run_reference,
            dependencies_by_reference=[dependency_task_reference],
        )
        all_tasks = dict()
        all_tasks[task_to_run_reference] = task_to_run
        all_tasks[dependency_task_reference] = dependency_task

        return task_to_run, all_tasks, list(all_tasks.keys())

    def test_has_dependencies_remaining_with_failed_dependencies(self):
        # setup
        (
            task_to_run,
            all_tasks,
            _,
        ) = self.generate_has_dependencies_remaining_with_failed_dependencies()

        expected_is_currently_blocked = True
        expected_is_permanently_blocked = True

        # exercise
        (
            actual_is_currently_blocked,
            actual_is_permanently_blocked,
        ) = self.sut.has_dependencies_remaining(task_to_run, all_tasks)

        # verify
        self.assertEqual(expected_is_currently_blocked, actual_is_currently_blocked)
        self.assertEqual(expected_is_permanently_blocked, actual_is_permanently_blocked)

    def test_get_next_task_to_run_with_failed_dependencies(self):
        # setup
        (
            _,
            all_tasks,
            tasks_to_run,
        ) = self.generate_has_dependencies_remaining_with_failed_dependencies()

        resources = dict()
        expected_next_task = None
        expected_should_shutdown = True

        # exercise
        (actual_next_task, actual_should_shutdown,) = self.sut.get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )

        # verify
        self.assertEqual(expected_next_task, actual_next_task)
        self.assertEqual(expected_should_shutdown, actual_should_shutdown)

    def generate_failed_dependencies_but_additional_tasks_are_present(self):
        all_tasks = dict()
        dependency_task = dict(
            task_reference=dependency_task_reference,
            dependencies_by_reference=[],
            QUEUE_STATUS=ERRORED,
        )
        all_tasks[dependency_task_reference] = dependency_task

        non_related_task = dict(
            task_reference=non_related_task_reference, dependencies_by_reference=[]
        )
        all_tasks[non_related_task_reference] = non_related_task

        task_to_run = dict(
            task_reference=task_to_run_reference,
            dependencies_by_reference=[dependency_task_reference],
        )
        all_tasks[task_to_run_reference] = task_to_run

        return task_to_run, all_tasks, list(all_tasks.keys())

    def test_has_dependencies_remaining_with_failed_dependencies_but_additional_tasks_are_present(
        self,
    ):
        # setup
        (
            task_to_run,
            all_tasks,
            _,
        ) = self.generate_failed_dependencies_but_additional_tasks_are_present()

        expected_is_currently_blocked = True
        expected_is_permanently_blocked = True

        # exercise
        (
            actual_is_currently_blocked,
            actual_is_permanently_blocked,
        ) = self.sut.has_dependencies_remaining(task_to_run, all_tasks)

        # verify
        self.assertEqual(expected_is_currently_blocked, actual_is_currently_blocked)
        self.assertEqual(expected_is_permanently_blocked, actual_is_permanently_blocked)

    def test_get_next_task_to_run_with_failed_dependencies_but_additional_tasks_are_present(
        self,
    ):
        # setup
        (
            _,
            all_tasks,
            tasks_to_run,
        ) = self.generate_failed_dependencies_but_additional_tasks_are_present()
        resources = dict()

        expected_next_task = all_tasks[non_related_task_reference]
        expected_should_shutdown = False

        # execute
        actual_next_task, actual_should_shutdown = self.sut.get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )

        # verify
        self.assertEqual(expected_should_shutdown, actual_should_shutdown)
        self.assertEqual(expected_next_task, actual_next_task)

    def generate_blocked_dependencies(self):
        all_tasks = dict()
        dependency_task = dict(
            task_reference=dependency_task_reference,
            dependencies_by_reference=[],
            QUEUE_STATUS=BLOCKED,
        )
        all_tasks[dependency_task_reference] = dependency_task

        task_to_run = dict(
            task_reference=task_to_run_reference,
            dependencies_by_reference=[dependency_task_reference],
        )
        all_tasks[task_to_run_reference] = task_to_run

        return task_to_run, all_tasks, list(all_tasks.keys())

    def test_has_dependencies_remaining_with_blocked_dependencies(self,):
        # setup
        (task_to_run, all_tasks, _,) = self.generate_blocked_dependencies()

        expected_is_currently_blocked = True
        expected_is_permanently_blocked = True

        # exercise
        (
            actual_is_currently_blocked,
            actual_is_permanently_blocked,
        ) = self.sut.has_dependencies_remaining(task_to_run, all_tasks)

        # verify
        self.assertEqual(expected_is_currently_blocked, actual_is_currently_blocked)
        self.assertEqual(expected_is_permanently_blocked, actual_is_permanently_blocked)

    def test_get_next_task_to_run_with_blocked_dependencies(self,):
        # setup
        (_, all_tasks, tasks_to_run,) = self.generate_blocked_dependencies()
        resources = dict()

        expected_next_task = None
        expected_should_shutdown = True

        # execute
        actual_next_task, actual_should_shutdown = self.sut.get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )

        # verify
        self.assertEqual(expected_should_shutdown, actual_should_shutdown)
        self.assertEqual(expected_next_task, actual_next_task)

    def generate_spoke_execution(self):
        all_tasks = {
            "create-policies": {
                "task_reference": "create-policies",
                "resources_required": [
                    "CLOUDFORMATION_CREATE_OR_UPDATE_eu-west-1_OF_XXXX"
                ],
                QUEUE_STATUS: COMPLETED,
            },
            constants.GENERATE_MANIFEST: {
                "task_reference": constants.GENERATE_MANIFEST,
                "dependencies_by_reference": ["create-policies"],
                QUEUE_STATUS: COMPLETED,
            },
            "run-deploy-in-spoke_YYYYY": {
                "task_reference": "run-deploy-in-spoke_YYYYY",
                "dependencies_by_reference": [constants.GENERATE_MANIFEST],
                QUEUE_STATUS: IN_PROGRESS,
            },
        }

        task_to_run = all_tasks.get("run-deploy-in-spoke_YYYYY")

        return task_to_run, all_tasks, list(all_tasks.keys())

    def test_has_dependencies_remaining_with_spoke_execution(self,):
        # setup
        (task_to_run, all_tasks, _,) = self.generate_spoke_execution()

        expected_is_currently_blocked = False
        expected_is_permanently_blocked = False

        # exercise
        (
            actual_is_currently_blocked,
            actual_is_permanently_blocked,
        ) = self.sut.has_dependencies_remaining(task_to_run, all_tasks)

        # verify
        self.assertEqual(expected_is_currently_blocked, actual_is_currently_blocked)
        self.assertEqual(expected_is_permanently_blocked, actual_is_permanently_blocked)

    def test_get_next_task_to_run_with_spoke_execution(self,):
        # setup
        (_, all_tasks, tasks_to_run,) = self.generate_spoke_execution()
        resources = dict()

        expected_next_task = None
        expected_should_shutdown = False

        # execute
        actual_next_task, actual_should_shutdown = self.sut.get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )

        # verify
        self.assertEqual(expected_should_shutdown, actual_should_shutdown)
        self.assertEqual(expected_next_task, actual_next_task)

    def generate_missing_generate_policies(self):
        all_tasks = {
            "non-specific-task": {
                "task_reference": "non-specific-task",
                "dependencies_by_reference": ["create-policies"],
            },
        }

        task_to_run = all_tasks.get("non-specific-task")

        return task_to_run, all_tasks, list(all_tasks.keys())

    def test_has_dependencies_remaining_with_missing_generate_policies(self,):
        # setup
        (task_to_run, all_tasks, _,) = self.generate_missing_generate_policies()

        expected_is_currently_blocked = False
        expected_is_permanently_blocked = False

        # exercise
        (
            actual_is_currently_blocked,
            actual_is_permanently_blocked,
        ) = self.sut.has_dependencies_remaining(task_to_run, all_tasks)

        # verify
        self.assertEqual(expected_is_currently_blocked, actual_is_currently_blocked)
        self.assertEqual(expected_is_permanently_blocked, actual_is_permanently_blocked)

    def test_get_next_task_to_run_with_missing_generate_policies(self,):
        # setup
        (_, all_tasks, tasks_to_run,) = self.generate_missing_generate_policies()
        resources = dict()

        expected_next_task = all_tasks.get("non-specific-task")
        expected_should_shutdown = False

        # execute
        actual_next_task, actual_should_shutdown = self.sut.get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )

        # verify
        self.assertEqual(expected_should_shutdown, actual_should_shutdown)
        self.assertEqual(expected_next_task, actual_next_task)
