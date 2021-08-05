from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.apps import app_base_task
from servicecatalog_puppet.workflow.apps import app_for_account_and_region_task
from servicecatalog_puppet.workflow.apps import app_for_account_task
from servicecatalog_puppet.workflow.apps import app_for_region_task
from servicecatalog_puppet.workflow.apps import app_task
from servicecatalog_puppet.workflow.generate import generate_policies_task
from servicecatalog_puppet.workflow.manifest import section_task


class AppSectionTask(
    app_base_task.AppBaseTask, section_task.SectionTask
):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        r = dict()
        requirements = list()
        r['items'] = requirements
        has_items = False

        for name, details in self.manifest.get(constants.APPS, {}).items():
            requirements += self.handle_requirements_for(
                name,
                constants.APP,
                constants.APPS,
                app_for_region_task.AppForRegionTask,
                app_for_account_task.AppForAccountTask,
                app_for_account_and_region_task.AppForAccountAndRegionTask,
                app_task.AppTask,
                dict(
                    app_name=name,
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                ),
            )
            has_items = True

        if has_items:
            generate_policies = list()
            r['generate_policies'] = generate_policies
            for (
                    region_name,
                    sharing_policies,
            ) in self.manifest.get_sharing_policies_by_region().items():
                generate_policies.append(
                    generate_policies_task.GeneratePolicies(
                        puppet_account_id=self.puppet_account_id,
                        manifest_file_path=self.manifest_file_path,
                        region=region_name,
                        sharing_policies=sharing_policies,
                    )
                )

        return r

    def run(self):
        self.write_output(self.manifest.get(self.section_name))
