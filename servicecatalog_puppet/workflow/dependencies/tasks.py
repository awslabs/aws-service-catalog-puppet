#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

from servicecatalog_puppet import yaml_utils
from servicecatalog_puppet.workflow import tasks
import luigi
from servicecatalog_puppet.workflow.general import get_ssm_param_task
from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    create,
)


class TaskWithReference(tasks.PuppetTask):
    task_reference = luigi.Parameter()
    manifest_task_reference_file_path = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()
    puppet_account_id = luigi.Parameter()

    def requires(self):
        return dict(reference_dependencies=self.get_dependencies_for_task_reference())

    def get_output_from_reference_dependency(self, reference):
        return json.loads(
            self.input().get("reference_dependencies").get(reference).open("r").read()
        )

    def get_dependencies_for_task_reference(self):
        dependencies = dict()
        reference = yaml_utils.load(
            open(self.manifest_task_reference_file_path, "r").read()
        ).get("all_tasks")
        this_task = reference.get(self.task_reference)
        for dependency_by_reference in this_task.get("dependencies_by_reference", []):
            dependency_by_reference_params = reference.get(dependency_by_reference)
            t_reference = dependency_by_reference_params.get("task_reference")
            dependencies[t_reference] = create(
                self.manifest_task_reference_file_path,
                self.puppet_account_id,
                dependency_by_reference_params,
            )
        return dependencies


class TaskWithParameters(
    TaskWithReference, get_ssm_param_task.PuppetTaskWithParameters  # TODO move here?
):
    pass


def unwrap(what):
    if hasattr(what, "get_wrapped"):
        return unwrap(what.get_wrapped())

    if isinstance(what, dict):
        thing = dict()
        for k, v in what.items():
            thing[k] = unwrap(v)
        return thing

    if isinstance(what, tuple):
        thing = list()
        for v in what:
            thing.append(unwrap(v))
        return thing

    if isinstance(what, list):
        thing = list()
        for v in what:
            thing.append(unwrap(v))
        return thing

    return what