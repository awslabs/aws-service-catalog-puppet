#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import luigi

from servicecatalog_puppet.workflow.dependencies import tasks


class GetOrCreateOrganizationalUnitTask(tasks.TaskWithReference):
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    path = luigi.Parameter()
    parent_ou_id = luigi.Parameter()
    name = luigi.Parameter()
    tags = luigi.ListParameter()
    parent_ou_task_ref = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "region": self.region,
            "path": self.path,
            "parent_ou_id": self.parent_ou_id,
            "name": self.name,
            "task_reference": self.task_reference,
            "cache_invalidator": self.cache_invalidator,
        }

    def find_ou_in_parent(self, orgs, parent_id):
        paginator = orgs.get_paginator("list_children")
        for page in paginator.paginate(
            ParentId=parent_id, ChildType="ORGANIZATIONAL_UNIT"
        ):
            for child in page.get("Children", []):
                child_details = orgs.describe_organizational_unit(
                    OrganizationalUnitId=child.get("Id")
                ).get("OrganizationalUnit")
                if child_details.get("Name") == self.name:
                    return child_details.get("Id")
        return None

    def run(self):
        with self.organizations_policy_client() as orgs:
            if self.path == "/":
                result = [orgs.convert_path_to_ou(self.path)]
            else:
                result = self.get_output_from_reference_dependency(
                    self.parent_ou_task_ref
                )
                parent_id = result[-1]
                ou_id = self.find_ou_in_parent(orgs, parent_id)
                if ou_id:
                    result.append(ou_id)
                else:
                    organizational_unit = orgs.create_organizational_unit(
                        ParentId=parent_id,
                        Name=self.name,
                        Tags=[
                            dict(Key=tag.get("Key"), Value=tag.get("Value"))
                            for tag in self.tags
                        ],
                    ).get("OrganizationalUnit")
                    result.append(organizational_unit.get("Id"))

        self.write_output(result)
