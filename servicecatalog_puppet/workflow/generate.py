import json
from functools import lru_cache

import luigi

from servicecatalog_puppet import config, constants

from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import (
    portfoliomanagement as portfoliomanagement_tasks,
)
from servicecatalog_puppet.workflow import general as general_tasks
from servicecatalog_puppet.workflow import tasks
from betterboto import client as betterboto_client


class GeneratePoliciesTemplate(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    manifest_file_path = luigi.Parameter()
    region = luigi.Parameter()
    sharing_policies = luigi.DictParameter()

    cache_invalidator = luigi.Parameter()

    @property
    def output_suffix(self):
        return "template.yaml"

    def params_for_results_display(self):
        return {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        if len(self.sharing_policies.get("accounts")) > 50:
            self.warning(
                "You have specified more than 50 accounts will not create the eventbus policy and spoke execution mode will not work"
            )
        rendered = config.env.get_template("policies.template.yaml.j2").render(
            sharing_policies=self.sharing_policies,
            VERSION=config.get_puppet_version(),
            HOME_REGION=self.region,
        )
        with self.output().open("w") as output_file:
            output_file.write(rendered)


class EnsureEventBridgeEventBusTask(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
        }

    def api_calls_used(self):
        return {
            f"events.describe_event_bus_{self.puppet_account_id}_{self.region}": 1,
            f"events.create_event_bus_{self.puppet_account_id}_{self.region}": 1,
        }

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
            "events",
            config.get_puppet_role_arn(self.puppet_account_id),
            f"events-{self.puppet_account_id}-{self.region}",
            region_name=self.region,
        ) as events:
            created = False
            try:
                events.describe_event_bus(Name=constants.EVENT_BUS_NAME)
                created = True
            except events.exceptions.ResourceNotFoundException:
                events.create_event_bus(Name=constants.EVENT_BUS_NAME)
        self.write_output(created)


class GeneratePolicies(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    manifest_file_path = luigi.Parameter()
    region = luigi.Parameter()
    sharing_policies = luigi.DictParameter()
    should_use_sns = luigi.BoolParameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "should_use_sns": self.should_use_sns,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "template": GeneratePoliciesTemplate(
                puppet_account_id=self.puppet_account_id,
                manifest_file_path=self.manifest_file_path,
                region=self.region,
                sharing_policies=self.sharing_policies,
                cache_invalidator=self.cache_invalidator,
            ),
        }

    def api_calls_used(self):
        return {
            f"cloudformation.create_or_update_{self.puppet_account_id}_{self.region}": 1,
        }

    def run(self):
        template = self.read_from_input("template")
        with betterboto_client.CrossAccountClientContextManager(
            "cloudformation",
            config.get_puppet_role_arn(self.puppet_account_id),
            f"cf-{self.puppet_account_id}-{self.region}",
            region_name=self.region,
        ) as cloudformation:
            self.info(template)
            cloudformation.create_or_update(
                ShouldUseChangeSets=False,
                StackName="servicecatalog-puppet-policies",
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
            )
        self.write_output(self.get_sharing_policies())

    @lru_cache()
    def get_sharing_policies(self):
        return json.loads(json.dumps(self.sharing_policies.get_wrapped()))


class GenerateSharesTask(tasks.PuppetTask, manifest_tasks.ManifestMixen):
    puppet_account_id = luigi.Parameter()
    manifest_file_path = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    section = luigi.Parameter()
    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "section": self.section,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        portfolios = dict()
        requirements = dict(
            deletes=list(),
            ensure_event_buses=list(),
            generate_policies=list(),
            portfolios=portfolios,
        )
        for region_name, accounts in self.manifest.get_accounts_by_region().items():
            requirements["deletes"].append(
                general_tasks.DeleteCloudFormationStackTask(
                    account_id=self.puppet_account_id,
                    region=region_name,
                    stack_name="servicecatalog-puppet-shares",
                )
            )

        for (
            region_name,
            sharing_policies,
        ) in self.manifest.get_sharing_policies_by_region().items():
            requirements["ensure_event_buses"].append(
                EnsureEventBridgeEventBusTask(
                    puppet_account_id=self.puppet_account_id, region=region_name,
                )
            )

            requirements["generate_policies"].append(
                GeneratePolicies(
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                    region=region_name,
                    sharing_policies=sharing_policies,
                    should_use_sns=self.should_use_sns,
                    cache_invalidator=self.cache_invalidator,
                )
            )

        for (
            region_name,
            shares_by_portfolio_account,
        ) in self.manifest.get_shares_by_region_portfolio_account(
            self.puppet_account_id, self.section
        ).items():
            for (
                portfolio_name,
                shares_by_account,
            ) in shares_by_portfolio_account.items():
                for account_id, share in shares_by_account.items():
                    i = "_".join(
                        [
                            str(self.puppet_account_id),
                            portfolio_name,
                            str(account_id),
                            region_name,
                        ]
                    )
                    portfolios[
                        i
                    ] = portfoliomanagement_tasks.GetPortfolioByPortfolioName(
                        manifest_file_path=self.manifest_file_path,
                        puppet_account_id=self.puppet_account_id,
                        portfolio=portfolio_name,
                        account_id=self.puppet_account_id,
                        region=region_name,
                        cache_invalidator=self.cache_invalidator,
                    )
        return requirements

    def run(self):
        tasks = list()
        for (
            region_name,
            shares_by_portfolio_account,
        ) in self.manifest.get_shares_by_region_portfolio_account(
            self.puppet_account_id, self.section
        ).items():
            for (
                portfolio_name,
                shares_by_account,
            ) in shares_by_portfolio_account.items():
                for account_id, share in shares_by_account.items():
                    i = "_".join(
                        [
                            str(self.puppet_account_id),
                            portfolio_name,
                            str(account_id),
                            region_name,
                        ]
                    )
                    portfolio_input = self.input().get("portfolios").get(i)

                    if portfolio_input is None:
                        raise Exception(
                            f"failed to get portfolios details for {i} in {self.input().get('portfolios')}"
                        )

                    portfolio = json.loads(portfolio_input.open("r").read())

                    tasks.append(
                        portfoliomanagement_tasks.CreateShareForAccountLaunchRegion(
                            manifest_file_path=self.manifest_file_path,
                            puppet_account_id=self.puppet_account_id,
                            account_id=account_id,
                            region=region_name,
                            portfolio=portfolio_name,
                            portfolio_id=portfolio.get("portfolio_id"),
                            sharing_mode=share.get(self.section).get(
                                "sharing_mode",
                                config.get_global_sharing_mode_default(
                                    self.puppet_account_id
                                ),
                            ),
                        )
                    )

        yield tasks
        self.write_output(self.params_for_results_display())
