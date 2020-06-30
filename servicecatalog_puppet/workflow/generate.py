import luigi
from servicecatalog_puppet import config

from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import portfoliomanagement as portfoliomanagement_tasks
from servicecatalog_puppet.workflow import general as general_tasks
from betterboto import client as betterboto_client


class GeneratePoliciesTemplate(manifest_tasks.SectionTask):
    region = luigi.Parameter()
    sharing_policies = luigi.DictParameter()

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.uid}.template.yaml"
        )

    def params_for_results_display(self):
        return {
            'region': self.region,
            'puppet_account_id': self.puppet_account_id,
            'manifest_file_path': self.manifest_file_path,
        }

    def run(self):
        rendered = config.env.get_template('policies.template.yaml.j2').render(
            sharing_policies=self.sharing_policies,
            VERSION=config.get_puppet_version(),
        )
        with self.output().open('w') as output_file:
            output_file.write(rendered)


class GeneratePolicies(manifest_tasks.SectionTask):
    region = luigi.Parameter()
    sharing_policies = luigi.DictParameter()

    def params_for_results_display(self):
        return {
            'region': self.region,
            'puppet_account_id': self.puppet_account_id,
            'manifest_file_path': self.manifest_file_path,
        }

    def requires(self):
        return {
            'template': GeneratePoliciesTemplate(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                should_use_sns=self.should_use_sns,
                should_use_product_plans=self.should_use_product_plans,
                include_expanded_from=self.include_expanded_from,
                single_account=self.single_account,
                is_dry_run=self.is_dry_run,
                execution_mode=self.execution_mode,
                region=self.region,
                sharing_policies=self.sharing_policies,
            )
        }

    def run(self):
        template = self.read_from_input('template')
        with betterboto_client.ClientContextManager('cloudformation', region_name=self.region) as cloudformation:
            cloudformation.create_or_update(
                StackName="servicecatalog-puppet-policies",
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:aws:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ] if self.should_use_sns else [],
            )
        self.write_output({})


class GenerateSharesTask(manifest_tasks.SectionTask):
    def params_for_results_display(self):
        return {
            'puppet_account_id': self.puppet_account_id,
            'manifest_file_path': self.manifest_file_path,
        }

    def run(self):
        for region_name, accounts in self.manifest.get_accounts_by_region().items():
            yield general_tasks.DeleteCloudFormationStackTask(
                account_id=self.puppet_account_id,
                region=region_name,
                stack_name="servicecatalog-puppet-shares"
            )

        for region_name, sharing_policies in self.manifest.get_sharing_policies_by_region().items():
            yield GeneratePolicies(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                should_use_sns=self.should_use_sns,
                should_use_product_plans=self.should_use_product_plans,
                include_expanded_from=self.include_expanded_from,
                single_account=self.single_account,
                is_dry_run=self.is_dry_run,
                execution_mode=self.execution_mode,
                region=region_name,
                sharing_policies=sharing_policies
            )

        for region_name, shares_by_portfolio_account in self.manifest.get_shares_by_region_portfolio_account().items():
            for portfolio_name, shares_by_account in shares_by_portfolio_account.items():
                for account_id, share in shares_by_account.items():
                    yield portfoliomanagement_tasks.CreateShareForAccountLaunchRegion(
                        manifest_file_path=self.manifest_file_path,
                        puppet_account_id=self.puppet_account_id,
                        account_id=account_id,
                        region=region_name,
                        portfolio=portfolio_name
                    )

        self.write_output(self.params_for_results_display())
