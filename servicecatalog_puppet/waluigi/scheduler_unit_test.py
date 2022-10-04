# #  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# #  SPDX-License-Identifier: Apache-2.0
# import os
# from unittest import mock as mocker
# from unittest.mock import call
#
#
# def get_tasks():
#     task_a = {
#         "puppet_account_id": "000000000000",
#         "task_reference": "A",
#         "dependencies_by_reference": [],
#         "account_id": "111111111111",
#         "region": "us-east-1",
#         "portfolio": "DepsRefactor5",
#         "sharing_mode": "AWS_ORGANIZATIONS",
#         "section_name": "portfolio-imported",
#         "manifest_section_names": {"launches": True},
#         "manifest_item_names": {"sleepFor10": True},
#         "manifest_account_ids": {"648052676434": True},
#         "resources_required": [
#             "SERVICE_CATALOG_LIST_ACCEPTED_PORTFOLIO_SHARES_us-east-1_OF_111111111111"
#         ],
#     }
#
#     task_b = {
#         "puppet_account_id": "000000000000",
#         "task_reference": "B",
#         "dependencies_by_reference": [],
#         "account_id": "222222222222",
#         "region": "us-east-1",
#         "portfolio": "DepsRefactor5",
#         "sharing_mode": "AWS_ORGANIZATIONS",
#         "section_name": "portfolio-imported",
#         "manifest_section_names": {"launches": True},
#         "manifest_item_names": {"sleepFor10": True},
#         "manifest_account_ids": {"648052676434": True},
#         "resources_required": [
#             "SERVICE_CATALOG_LIST_ACCEPTED_PORTFOLIO_SHARES_us-east-1_OF_222222222222"
#         ],
#     }
#
#     task_c = {
#         "puppet_account_id": "000000000000",
#         "task_reference": "C",
#         "dependencies_by_reference": [],
#         "account_id": "333333333333",
#         "region": "us-east-1",
#         "portfolio": "DepsRefactor5",
#         "sharing_mode": "AWS_ORGANIZATIONS",
#         "section_name": "portfolio-imported",
#         "manifest_section_names": {"launches": True},
#         "manifest_item_names": {"sleepFor10": True},
#         "manifest_account_ids": {"648052676434": True},
#         "resources_required": [
#             "SERVICE_CATALOG_LIST_ACCEPTED_PORTFOLIO_SHARES_us-east-1_OF_333333333333"
#         ],
#     }
#
#     return task_a, task_b, task_c
#
#
# def test_get_next_tasks_to_run_for_task_with_no_deps():
#     # setup
#     from servicecatalog_puppet.waluigi import scheduler as sut
#
#     task_a, task_b, task_c = get_tasks()
#
#     tasks_in_order = [
#         task_a.get("task_reference"),
#         task_b.get("task_reference"),
#         task_c.get("task_reference"),
#     ]
#     tasks_to_run = {
#         task_a.get("task_reference"): task_a,
#         task_b.get("task_reference"): task_b,
#         task_c.get("task_reference"): task_c,
#     }
#     task_to_maybe_run = task_b
#     resources_in_use = dict()
#     expected_result = task_b
#
#     # exercise
#     actual_result = sut.get_next_tasks_to_run_for_task(
#         task_to_maybe_run, tasks_in_order, tasks_to_run, resources_in_use
#     )
#
#     # verify
#     assert expected_result.get("task_reference") == actual_result.get("task_reference")
#
#
# def test_get_next_task_to_run_with_no_deps():
#     # setup
#     from servicecatalog_puppet.waluigi import scheduler as sut
#
#     task_a, task_b, task_c = get_tasks()
#
#     tasks_in_order = [
#         task_a.get("task_reference"),
#         task_b.get("task_reference"),
#         task_c.get("task_reference"),
#     ]
#     tasks_to_run = {
#         task_a.get("task_reference"): task_a,
#         task_b.get("task_reference"): task_b,
#         task_c.get("task_reference"): task_c,
#     }
#     resources_in_use = dict()
#     expected_result = task_a.get("task_reference")
#
#     # exercise
#     actual_result = sut.get_next_task_to_run(
#         tasks_in_order, tasks_to_run, resources_in_use
#     ).get("task_reference")
#
#     # verify
#     assert expected_result == actual_result
#
#
# def test_get_next_tasks_to_run_for_task_with_deps():
#     # setup
#     from servicecatalog_puppet.waluigi import scheduler as sut
#
#     task_a, task_b, task_c = get_tasks()
#
#     tasks_in_order = [
#         task_a.get("task_reference"),
#         task_b.get("task_reference"),
#         task_c.get("task_reference"),
#     ]
#     tasks_to_run = {
#         task_a.get("task_reference"): task_a,
#         task_b.get("task_reference"): task_b,
#         task_c.get("task_reference"): task_c,
#     }
#     task_to_maybe_run = task_b
#     task_b["dependencies_by_reference"] = task_a.get("task_reference")
#     resources_in_use = dict()
#     expected_result = task_a
#
#     # exercise
#     actual_result = sut.get_next_tasks_to_run_for_task(
#         task_to_maybe_run, tasks_in_order, tasks_to_run, resources_in_use
#     )
#
#     # verify
#     assert expected_result.get("task_reference") == actual_result.get("task_reference")
#
#
# def test_get_next_task_to_run_with_deps():
#     # setup
#     from servicecatalog_puppet.waluigi import scheduler as sut
#
#     task_a, task_b, task_c = get_tasks()
#
#     tasks_in_order = [
#         task_a.get("task_reference"),
#         task_b.get("task_reference"),
#         task_c.get("task_reference"),
#     ]
#     tasks_to_run = {
#         task_a.get("task_reference"): task_a,
#         task_b.get("task_reference"): task_b,
#         task_c.get("task_reference"): task_c,
#     }
#     resources_in_use = dict()
#     task_a["dependencies_by_reference"] = task_b.get("task_reference")
#     expected_result = task_b.get("task_reference")
#
#     # exercise
#     actual_result = sut.get_next_task_to_run(
#         tasks_in_order, tasks_to_run, resources_in_use
#     ).get("task_reference")
#
#     # verify
#     assert expected_result == actual_result
#
#
# def test_get_next_tasks_to_run_for_task_with_deps_running():
#     # setup
#     from servicecatalog_puppet.waluigi import scheduler as sut
#
#     task_a, task_b, task_c = get_tasks()
#
#     tasks_in_order = [
#         task_a.get("task_reference"),
#         task_b.get("task_reference"),
#         task_c.get("task_reference"),
#     ]
#     tasks_to_run = {
#         task_a.get("task_reference"): task_a,
#         task_b.get("task_reference"): task_b,
#         task_c.get("task_reference"): task_c,
#     }
#     task_to_maybe_run = task_b
#     task_a[sut.QUEUE_STATUS] = sut.PENDING
#     task_b["dependencies_by_reference"] = task_a.get("task_reference")
#
#     resources_in_use = dict()
#     expected_result = None
#
#     # exercise
#     actual_result = sut.get_next_tasks_to_run_for_task(
#         task_to_maybe_run, tasks_in_order, tasks_to_run, resources_in_use
#     )
#
#     # verify
#     assert expected_result == actual_result
#
#
# def test_get_next_task_to_run_with_deps_running():
#     # setup
#     from servicecatalog_puppet.waluigi import scheduler as sut
#
#     task_a, task_b, task_c = get_tasks()
#
#     tasks_in_order = [
#         task_a.get("task_reference"),
#         task_b.get("task_reference"),
#         task_c.get("task_reference"),
#     ]
#     tasks_to_run = {
#         task_a.get("task_reference"): task_a,
#         task_b.get("task_reference"): task_b,
#         task_c.get("task_reference"): task_c,
#     }
#     resources_in_use = dict()
#     task_a["dependencies_by_reference"] = task_b.get("task_reference")
#     task_b[sut.QUEUE_STATUS] = sut.PENDING
#     expected_result = task_c.get("task_reference")
#
#     # exercise
#     actual_result = sut.get_next_task_to_run(
#         tasks_in_order, tasks_to_run, resources_in_use
#     ).get("task_reference")
#
#     # verify
#     assert expected_result == actual_result
