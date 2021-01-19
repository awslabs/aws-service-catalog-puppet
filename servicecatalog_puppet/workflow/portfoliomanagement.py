import json

import os
import re
import time
from functools import lru_cache

import luigi
from betterboto import client as betterboto_client

from servicecatalog_puppet import aws
from servicecatalog_puppet import config
from servicecatalog_puppet import constants

from servicecatalog_puppet.workflow import tasks, general

from servicecatalog_puppet.workflow import manifest as manifest_tasks

import yaml


class PortfolioManagementTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()


class GetVersionDetailsByNames(PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product": self.product,
            "version": self.version,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        portfolio_details = yield GetPortfolioByPortfolioName(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            portfolio=self.portfolio,
            account_id=self.account_id,
            region=self.region,
            cache_invalidator=self.cache_invalidator,
        )
        portfolio_details = json.loads(portfolio_details.open("r").read())

        product_details = yield GetProductIdByProductName(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            portfolio=self.portfolio,
            portfolio_id=portfolio_details.get("portfolio_id"),
            product=self.product,
            account_id=self.account_id,
            region=self.region,
            cache_invalidator=self.cache_invalidator,
        )
        product_details = json.loads(product_details.open("r").read())

        version_details = yield GetVersionIdByVersionName(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            portfolio=self.portfolio,
            portfolio_id=portfolio_details.get("portfolio_id"),
            product=self.product,
            product_id=product_details.get("product_id"),
            version=self.version,
            account_id=self.account_id,
            region=self.region,
            cache_invalidator=self.cache_invalidator,
        )
        version_details = json.loads(version_details.open("r").read())

        self.write_output(
            dict(
                portfolio_details=portfolio_details,
                product_details=product_details,
                version_details=version_details,
            )
        )


class GetVersionIdByVersionName(PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    product = luigi.Parameter()
    product_id = luigi.Parameter()
    version = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_provisioning_artifacts_{self.account_id}_{self.region}",
        ]

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}",
            region_name=self.region,
        ) as cross_account_servicecatalog:
            version_id = aws.get_version_id_for(
                cross_account_servicecatalog, self.product_id, self.version,
            )
            with self.output().open("w") as f:
                f.write(
                    json.dumps(
                        {
                            "version_name": self.version,
                            "version_id": version_id,
                            "product_name": self.product,
                            "product_id": self.product_id,
                        },
                        indent=4,
                        default=str,
                    )
                )


class SearchProductsAsAdminTask(PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.search_products_as_admin_{self.account_id}_{self.region}",
        ]

    def run(self):
        role = config.get_puppet_role_arn(self.account_id)
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            role,
            f"sc-{self.account_id}-{self.region}",
            region_name=self.region,
        ) as spoke_service_catalog:
            results = spoke_service_catalog.search_products_as_admin_single_page(
                PortfolioId=self.portfolio_id,
            )
            self.write_output(results)


class GetProductIdByProductName(PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    product = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "product": self.product,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "search_products_as_admin": SearchProductsAsAdminTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                account_id=self.account_id,
                region=self.region,
                cache_invalidator=self.cache_invalidator,
            ),
        }

    def run(self):
        product_id = None
        response = self.load_from_input("search_products_as_admin")
        for product_view_details in response.get("ProductViewDetails"):
            product_view = product_view_details.get("ProductViewSummary")
            self.info(f"looking at product: {product_view.get('Name')}")
            if product_view.get("Name") == self.product:
                self.info("Found product: {}".format(product_view))
                product_id = product_view.get("ProductId")
        assert product_id is not None, "Did not find product looking for"
        self.write_output(
            {
                "product_name": self.product,
                "product_id": product_id,
                "portfolio_name": self.portfolio,
                "portfolio_id": self.portfolio_id,
            }
        )


class GetPortfolioByPortfolioName(PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_accepted_portfolio_shares_single_page{self.account_id}_{self.region}",
            f"servicecatalog.list_portfolios_{self.account_id}_{self.region}",
        ]

    def complete(self):
        target_created = super().complete()
        if target_created:
            t = self.output().open("r").read()
            j = json.loads(t)
            result = self.get_portfolio()
            if j.get("portfolio_id") == result.get("Id"):
                return True
            else:
                self.write_output(
                    {
                        "portfolio_name": self.portfolio,
                        "portfolio_id": result.get("Id"),
                        "provider_name": result.get("ProviderName"),
                        "description": result.get("Description"),
                    }
                )
                return True
        else:
            return False

    @lru_cache()
    def get_portfolio(self):
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}",
            region_name=self.region,
        ) as cross_account_servicecatalog:
            result = None
            response = (
                cross_account_servicecatalog.list_accepted_portfolio_shares_single_page()
            )
            for portfolio_detail in response.get("PortfolioDetails"):
                if portfolio_detail.get("DisplayName") == self.portfolio:
                    result = portfolio_detail
                    break

            if result is None:
                response = cross_account_servicecatalog.list_portfolios_single_page()
                for portfolio_detail in response.get("PortfolioDetails", []):
                    if portfolio_detail.get("DisplayName") == self.portfolio:
                        result = portfolio_detail
                        break

            assert result is not None, "Could not find portfolio"
            return result

    def run(self):
        result = self.get_portfolio()
        self.write_output(
            {
                "portfolio_name": self.portfolio,
                "portfolio_id": result.get("Id"),
                "provider_name": result.get("ProviderName"),
                "description": result.get("Description"),
            }
        )


class ProvisionActionTask(PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    source = luigi.Parameter()
    phase = luigi.Parameter()
    source_type = luigi.Parameter()
    type = luigi.Parameter()
    name = luigi.Parameter()
    project_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    parameters = luigi.DictParameter(default={})

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "type": self.type,
            "source": self.source,
            "phase": self.phase,
            "source_type": self.source_type,
            "name": self.name,
            "project_name": self.project_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        ssm_params = {}
        for param_name, param_details in self.parameters.items():
            if param_details.get("ssm"):
                if param_details.get("default"):
                    del param_details["default"]
                ssm_parameter_name = param_details.get("ssm").get("name")
                ssm_parameter_name = ssm_parameter_name.replace(
                    "${AWS::Region}", self.region
                )
                ssm_parameter_name = ssm_parameter_name.replace(
                    "${AWS::AccountId}", self.account_id
                )
                ssm_params[param_name] = tasks.GetSSMParamTask(
                    parameter_name=param_name,
                    name=ssm_parameter_name,
                    region=param_details.get("ssm").get(
                        "region", config.get_home_region(self.puppet_account_id)
                    ),
                    cache_invalidator=self.cache_invalidator,
                )
        return {
            "ssm_params": ssm_params,
        }

    def api_calls_used(self):
        return [
            f"codebuild.start_build_and_wait_for_completion_({self.account_id}_{self.region}",
        ]

    def run(self):
        all_params = {}
        for param_name, param_details in self.parameters.items():
            if param_details.get("ssm"):
                with self.input().get("ssm_params").get(param_name).open() as f:
                    all_params[param_name] = json.loads(f.read()).get("Value")
            if param_details.get("default"):
                all_params[param_name] = param_details.get("default")
        self.info(f"finished collecting all_params: {all_params}")

        environment_variables_override = [
            {"name": param_name, "value": param_details, "type": "PLAINTEXT"}
            for param_name, param_details in all_params.items()
        ]
        role = config.get_puppet_role_arn(self.account_id)
        with betterboto_client.CrossAccountClientContextManager(
            "codebuild",
            role,
            f"sc-{self.region}-{self.account_id}",
            region_name=self.region,
        ) as codebuild:
            build = codebuild.start_build_and_wait_for_completion(
                projectName=self.project_name,
                environmentVariablesOverride=environment_variables_override,
            )
            if build.get("buildStatus") != "SUCCEEDED":
                raise Exception(f"{self.uid}: Build failed: {build.get('buildStatus')}")
        self.write_output(self.param_kwargs)


class CreateSpokeLocalPortfolioTask(
    PortfolioManagementTask, manifest_tasks.ManifestMixen
):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    organization = luigi.Parameter(significant=False)
    sharing_mode = luigi.Parameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
            "sharing_mode": self.sharing_mode,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "create_share_for_account_launch_region": CreateShareForAccountLaunchRegion(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                account_id=self.account_id,
                region=self.region,
                sharing_mode=self.sharing_mode,
            ),
            "puppet_portfolio": GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.puppet_account_id,
                region=self.region,
                cache_invalidator=self.cache_invalidator,
            ),
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_portfolios_{self.account_id}_{self.region}",
            f"servicecatalog.create_portfolio_{self.account_id}_{self.region}",
        ]

    def run(self):
        role = config.get_puppet_role_arn(self.account_id)
        with self.input().get("puppet_portfolio").open("r") as f:
            portfolio_details = json.loads(f.read())
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            role,
            f"sc-{self.account_id}-{self.region}",
            region_name=self.region,
        ) as spoke_service_catalog:
            spoke_portfolio = aws.ensure_portfolio(
                spoke_service_catalog,
                self.portfolio,
                portfolio_details.get("provider_name"),
                portfolio_details.get("description"),
            )
        self.write_output(spoke_portfolio)


class CreateAssociationsForPortfolioTask(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    organization = luigi.Parameter()

    associations = luigi.ListParameter(default=[])

    should_use_sns = luigi.Parameter(significant=False, default=False)

    sharing_mode = luigi.Parameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
            "sharing_mode": self.sharing_mode,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "create_spoke_local_portfolio_task": CreateSpokeLocalPortfolioTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                organization=self.organization,
                sharing_mode=self.sharing_mode,
                cache_invalidator=self.cache_invalidator,
            ),
        }

    def api_calls_used(self):
        return [
            f"cloudformation.create_or_update_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
        ]

    def run(self):
        role = config.get_puppet_role_arn(self.account_id)

        with self.input().get("create_spoke_local_portfolio_task").open("r") as f:
            portfolio_id = json.loads(f.read()).get("Id")
        self.info(f"using portfolio_id: {portfolio_id}")

        with betterboto_client.CrossAccountClientContextManager(
            "cloudformation",
            role,
            f"cfn-{self.account_id}-{self.region}",
            region_name=self.region,
        ) as cloudformation:
            template = config.env.get_template("associations.template.yaml.j2").render(
                portfolio={
                    "DisplayName": self.portfolio,
                    "Associations": self.associations,
                },
                portfolio_id=portfolio_id,
            )
            stack_name = f"associations-for-portfolio-{portfolio_id}"
            self.info(template)
            cloudformation.create_or_update(
                StackName=stack_name,
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
            )
            result = cloudformation.describe_stacks(StackName=stack_name,).get(
                "Stacks"
            )[0]
            self.write_output(result)


class GetProductsAndProvisioningArtifactsTask(PortfolioManagementTask):
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "search_products_as_admin": SearchProductsAsAdminTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                region=self.region,
                account_id=self.puppet_account_id,
                cache_invalidator=self.cache_invalidator,
            )
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_provisioning_artifacts_{self.region}",
        ]

    def run(self):
        product_and_artifact_details = []
        with betterboto_client.ClientContextManager(
            "servicecatalog", region_name=self.region
        ) as service_catalog:
            response = self.load_from_input("search_products_as_admin")
            for product_view_detail in response.get("ProductViewDetails", []):
                product_view_summary = product_view_detail.get("ProductViewSummary")
                product_view_summary["ProductARN"] = product_view_detail.get(
                    "ProductARN"
                )
                product_and_artifact_details.append(product_view_summary)

                provisioning_artifact_details = product_view_summary[
                    "provisioning_artifact_details"
                ] = []
                hub_product_id = product_view_summary.get("ProductId")
                hub_provisioning_artifact_details = service_catalog.list_provisioning_artifacts(
                    ProductId=hub_product_id
                ).get(
                    "ProvisioningArtifactDetails", []
                )
                for (
                    hub_provisioning_artifact_detail
                ) in hub_provisioning_artifact_details:
                    if (
                        hub_provisioning_artifact_detail.get("Type")
                        == "CLOUD_FORMATION_TEMPLATE"
                    ):
                        provisioning_artifact_details.append(
                            hub_provisioning_artifact_detail
                        )

        self.write_output(product_and_artifact_details)


class CopyIntoSpokeLocalPortfolioTask(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    organization = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    sharing_mode = luigi.Parameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
            "sharing_mode": self.sharing_mode,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "create_spoke_local_portfolio": CreateSpokeLocalPortfolioTask(
                manifest_file_path=self.manifest_file_path,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                organization=self.organization,
                puppet_account_id=self.puppet_account_id,
                sharing_mode=self.sharing_mode,
                cache_invalidator=self.cache_invalidator,
            ),
            "products_and_provisioning_artifacts": GetProductsAndProvisioningArtifactsTask(
                manifest_file_path=self.manifest_file_path,
                region=self.region,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                puppet_account_id=self.puppet_account_id,
                cache_invalidator=self.cache_invalidator,
            ),
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.search_products_as_admin_{self.account_id}_{self.region}",
            f"servicecatalog.list_provisioning_artifacts_{self.account_id}_{self.region}",
            f"servicecatalog.copy_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_copy_product_status_{self.account_id}_{self.region}",
            f"servicecatalog.associate_product_with_portfolio_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioning_artifact_{self.account_id}_{self.region}",
        ]

    def run(self):
        with self.input().get("create_spoke_local_portfolio").open("r") as f:
            spoke_portfolio = json.loads(f.read())
        portfolio_id = spoke_portfolio.get("Id")
        product_versions_that_should_be_copied = {}
        product_versions_that_should_be_updated = {}

        product_name_to_id_dict = {}
        with self.input().get("products_and_provisioning_artifacts").open("r") as f:
            products_and_provisioning_artifacts = json.loads(f.read())
            for product_view_summary in products_and_provisioning_artifacts:
                spoke_product_id = False
                target_product_id = False
                hub_product_name = product_view_summary.get("Name")

                for hub_provisioning_artifact_detail in product_view_summary.get(
                    "provisioning_artifact_details", []
                ):
                    if (
                        hub_provisioning_artifact_detail.get("Type")
                        == "CLOUD_FORMATION_TEMPLATE"
                    ):
                        product_versions_that_should_be_copied[
                            f"{hub_provisioning_artifact_detail.get('Name')}"
                        ] = hub_provisioning_artifact_detail
                        product_versions_that_should_be_updated[
                            f"{hub_provisioning_artifact_detail.get('Name')}"
                        ] = hub_provisioning_artifact_detail

                self.info(f"Copying {hub_product_name}")
                hub_product_arn = product_view_summary.get("ProductARN")
                copy_args = {
                    "SourceProductArn": hub_product_arn,
                    "CopyOptions": ["CopyTags",],
                }

                role = config.get_puppet_role_arn(self.account_id)
                with betterboto_client.CrossAccountClientContextManager(
                    "servicecatalog",
                    role,
                    f"sc-{self.account_id}-{self.region}",
                    region_name=self.region,
                ) as spoke_service_catalog:
                    p = None
                    try:
                        p = spoke_service_catalog.search_products_as_admin_single_page(
                            PortfolioId=portfolio_id,
                            Filters={"FullTextSearch": [hub_product_name]},
                        )
                    except spoke_service_catalog.exceptions.ResourceNotFoundException as e:
                        self.info(f"swallowing exception: {str(e)}")

                    if p is not None:
                        for spoke_product_view_details in p.get("ProductViewDetails"):
                            spoke_product_view = spoke_product_view_details.get(
                                "ProductViewSummary"
                            )
                            if spoke_product_view.get("Name") == hub_product_name:
                                spoke_product_id = spoke_product_view.get("ProductId")
                                product_name_to_id_dict[
                                    hub_product_name
                                ] = spoke_product_id
                                copy_args["TargetProductId"] = spoke_product_id
                                spoke_provisioning_artifact_details = spoke_service_catalog.list_provisioning_artifacts(
                                    ProductId=spoke_product_id
                                ).get(
                                    "ProvisioningArtifactDetails"
                                )
                                for (
                                    provisioning_artifact_detail
                                ) in spoke_provisioning_artifact_details:
                                    id_to_delete = (
                                        f"{provisioning_artifact_detail.get('Name')}"
                                    )
                                    if (
                                        product_versions_that_should_be_copied.get(
                                            id_to_delete, None
                                        )
                                        is not None
                                    ):
                                        self.info(
                                            f"{hub_product_name} :: Going to skip {spoke_product_id} {provisioning_artifact_detail.get('Name')}"
                                        )
                                        del product_versions_that_should_be_copied[
                                            id_to_delete
                                        ]

                    if len(product_versions_that_should_be_copied.keys()) == 0:
                        self.info(f"no versions to copy")
                    else:
                        self.info(f"about to copy product")

                        copy_args["SourceProvisioningArtifactIdentifiers"] = [
                            {"Id": a.get("Id")}
                            for a in product_versions_that_should_be_copied.values()
                        ]

                        self.info(f"about to copy product with args: {copy_args}")
                        copy_product_token = spoke_service_catalog.copy_product(
                            **copy_args
                        ).get("CopyProductToken")
                        while True:
                            time.sleep(5)
                            r = spoke_service_catalog.describe_copy_product_status(
                                CopyProductToken=copy_product_token
                            )
                            target_product_id = r.get("TargetProductId")
                            self.info(
                                f"{hub_product_name} status: {r.get('CopyProductStatus')}"
                            )
                            if r.get("CopyProductStatus") == "FAILED":
                                raise Exception(
                                    f"Copying "
                                    f"{hub_product_name} failed: {r.get('StatusDetail')}"
                                )
                            elif r.get("CopyProductStatus") == "SUCCEEDED":
                                break

                        self.info(
                            f"adding {target_product_id} to portfolio {portfolio_id}"
                        )
                        spoke_service_catalog.associate_product_with_portfolio(
                            ProductId=target_product_id, PortfolioId=portfolio_id,
                        )

                        # associate_product_with_portfolio is not a synchronous request
                        self.info(
                            f"waiting for adding of {target_product_id} to portfolio {portfolio_id}"
                        )
                        while True:
                            time.sleep(2)
                            response = spoke_service_catalog.search_products_as_admin_single_page(
                                PortfolioId=portfolio_id,
                            )
                            products_ids = [
                                product_view_detail.get("ProductViewSummary").get(
                                    "ProductId"
                                )
                                for product_view_detail in response.get(
                                    "ProductViewDetails"
                                )
                            ]
                            self.info(
                                f"Looking for {target_product_id} in {products_ids}"
                            )

                            if target_product_id in products_ids:
                                break

                        product_name_to_id_dict[hub_product_name] = target_product_id

                    product_id_in_spoke = spoke_product_id or target_product_id
                    spoke_provisioning_artifact_details = spoke_service_catalog.list_provisioning_artifacts(
                        ProductId=product_id_in_spoke
                    ).get(
                        "ProvisioningArtifactDetails", []
                    )
                    for (
                        version_name,
                        version_details,
                    ) in product_versions_that_should_be_updated.items():
                        self.info(
                            f"{version_name} is active: {version_details.get('Active')} in hub"
                        )
                        for (
                            spoke_provisioning_artifact_detail
                        ) in spoke_provisioning_artifact_details:
                            if (
                                spoke_provisioning_artifact_detail.get("Name")
                                == version_name
                            ):
                                self.info(
                                    f"Updating active of {version_name}/{spoke_provisioning_artifact_detail.get('Id')} "
                                    f"in the spoke to {version_details.get('Active')}"
                                )
                                spoke_service_catalog.update_provisioning_artifact(
                                    ProductId=product_id_in_spoke,
                                    ProvisioningArtifactId=spoke_provisioning_artifact_detail.get(
                                        "Id"
                                    ),
                                    Active=version_details.get("Active"),
                                )

        with self.output().open("w") as f:
            f.write(
                json.dumps(
                    {
                        "portfolio": spoke_portfolio,
                        "product_versions_that_should_be_copied": product_versions_that_should_be_copied,
                        "products": product_name_to_id_dict,
                    },
                    indent=4,
                    default=str,
                )
            )


class ImportIntoSpokeLocalPortfolioTask(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    organization = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    sharing_mode = luigi.Parameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
            "sharing_mode": self.sharing_mode,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "create_spoke_local_portfolio": CreateSpokeLocalPortfolioTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                organization=self.organization,
                sharing_mode=self.sharing_mode,
                cache_invalidator=self.cache_invalidator,
            ),
            "products_and_provisioning_artifacts": GetProductsAndProvisioningArtifactsTask(
                manifest_file_path=self.manifest_file_path,
                region=self.region,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                puppet_account_id=self.puppet_account_id,
                cache_invalidator=self.cache_invalidator,
            ),
            "hub_portfolio": GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.puppet_account_id,
                region=self.region,
                cache_invalidator=self.cache_invalidator,
            ),
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.search_products_as_admin_{self.account_id}_{self.region}",
            f"servicecatalog.list_provisioning_artifacts_{self.account_id}_{self.region}",
            f"servicecatalog.associate_product_with_portfolio_{self.account_id}_{self.region}",
        ]

    def run(self):
        with self.input().get("create_spoke_local_portfolio").open("r") as f:
            spoke_portfolio = json.loads(f.read())
        portfolio_id = spoke_portfolio.get("Id")

        with self.input().get("hub_portfolio").open("r") as f:
            hub_portfolio = json.loads(f.read())
        hub_portfolio_id = hub_portfolio.get("portfolio_id")

        product_name_to_id_dict = {}
        hub_product_to_import_list = []

        with self.input().get("products_and_provisioning_artifacts").open("r") as f:
            products_and_provisioning_artifacts = json.loads(f.read())
            for product_view_summary in products_and_provisioning_artifacts:
                hub_product_name = product_view_summary.get("Name")
                hub_product_id = product_view_summary.get("ProductId")
                product_name_to_id_dict[hub_product_name] = hub_product_id
                hub_product_to_import_list.append(hub_product_id)

        self.info(f"Starting product import with targets {hub_product_to_import_list}")

        role = config.get_puppet_role_arn(self.account_id)
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            role,
            f"sc-{self.account_id}-{self.region}",
            region_name=self.region,
        ) as spoke_service_catalog:

            while True:
                self.info(f"Generating product list for portfolio {portfolio_id}")

                response = spoke_service_catalog.search_products_as_admin_single_page(
                    PortfolioId=portfolio_id,
                )
                spoke_portfolio_products = [
                    product_view_detail.get("ProductViewSummary").get("ProductId")
                    for product_view_detail in response.get("ProductViewDetails")
                ]

                target_products = [
                    product_id
                    for product_id in hub_product_to_import_list
                    if product_id not in spoke_portfolio_products
                ]

                if not target_products:
                    self.info(
                        f"No more products for import to portfolio {portfolio_id}"
                    )
                    break

                self.info(
                    f"Products {target_products} not yet imported to portfolio {portfolio_id}"
                )

                for product_id in target_products:
                    self.info(f"Associating {product_id}")
                    spoke_service_catalog.associate_product_with_portfolio(
                        ProductId=product_id,
                        PortfolioId=portfolio_id,
                        SourcePortfolioId=hub_portfolio_id,
                    )

                # associate_product_with_portfolio is not a synchronous request
                # so wait a short time, then try again with any products not yet appeared
                time.sleep(2)

        with self.output().open("w") as f:
            f.write(
                json.dumps(
                    {
                        "portfolio": spoke_portfolio,
                        "products": product_name_to_id_dict,
                    },
                    indent=4,
                    default=str,
                )
            )


class CreateLaunchRoleConstraintsForPortfolio(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    organization = luigi.Parameter()
    product_generation_method = luigi.Parameter()
    launch_constraints = luigi.DictParameter()
    should_use_sns = luigi.Parameter(default=False, significant=False)

    sharing_mode = luigi.Parameter()
    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
        }

    def requires(self):
        if self.product_generation_method == "import":
            return {
                "create_spoke_local_portfolio_task": ImportIntoSpokeLocalPortfolioTask(
                    manifest_file_path=self.manifest_file_path,
                    account_id=self.account_id,
                    region=self.region,
                    portfolio=self.portfolio,
                    portfolio_id=self.portfolio_id,
                    organization=self.organization,
                    puppet_account_id=self.puppet_account_id,
                    sharing_mode=self.sharing_mode,
                    cache_invalidator=self.cache_invalidator,
                ),
            }
        else:
            return {
                "create_spoke_local_portfolio_task": CopyIntoSpokeLocalPortfolioTask(
                    manifest_file_path=self.manifest_file_path,
                    account_id=self.account_id,
                    region=self.region,
                    portfolio=self.portfolio,
                    portfolio_id=self.portfolio_id,
                    organization=self.organization,
                    puppet_account_id=self.puppet_account_id,
                    sharing_mode=self.sharing_mode,
                    cache_invalidator=self.cache_invalidator,
                ),
            }

    def api_calls_used(self):
        return [
            f"cloudformation.ensure_deleted_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
            f"cloudformation.create_or_update_{self.account_id}_{self.region}",
            f"service_catalog.search_products_as_admin_{self.account_id}_{self.region}",
        ]

    def run(self):
        role = config.get_puppet_role_arn(self.account_id)
        with self.input().get("create_spoke_local_portfolio_task").open("r") as f:
            dependency_output = json.loads(f.read())
        spoke_portfolio = dependency_output.get("portfolio")
        portfolio_id = spoke_portfolio.get("Id")
        product_name_to_id_dict = dependency_output.get("products")
        with betterboto_client.CrossAccountClientContextManager(
            "cloudformation",
            role,
            f"cfn-{self.account_id}-{self.region}",
            region_name=self.region,
        ) as cloudformation:
            new_launch_constraints = []
            for launch_constraint in self.launch_constraints:
                new_launch_constraint = {
                    "products": [],
                    "roles": launch_constraint.get("roles"),
                }
                # DEBUG HERE to see why products list dict thing is empty
                if launch_constraint.get("products", None) is not None:
                    if isinstance(launch_constraint.get("products"), tuple):
                        new_launch_constraint["products"] += launch_constraint.get(
                            "products"
                        )
                    elif isinstance(launch_constraint.get("products"), str):
                        with betterboto_client.CrossAccountClientContextManager(
                            "servicecatalog",
                            role,
                            f"sc-{self.account_id}-{self.region}",
                            region_name=self.region,
                        ) as service_catalog:
                            response = service_catalog.search_products_as_admin_single_page(
                                PortfolioId=portfolio_id
                            )
                            for product_view_details in response.get(
                                "ProductViewDetails", []
                            ):
                                product_view_summary = product_view_details.get(
                                    "ProductViewSummary"
                                )
                                product_name_to_id_dict[
                                    product_view_summary.get("Name")
                                ] = product_view_summary.get("ProductId")
                                if re.match(
                                    launch_constraint.get("products"),
                                    product_view_summary.get("Name"),
                                ):
                                    new_launch_constraint["products"].append(
                                        product_view_summary.get("Name")
                                    )
                    else:
                        raise Exception(
                            f'Unexpected launch constraint type {type(launch_constraint.get("products"))}'
                        )

                if launch_constraint.get("product", None) is not None:
                    new_launch_constraint["products"].append(
                        launch_constraint.get("product")
                    )

                new_launch_constraints.append(new_launch_constraint)

            template = config.env.get_template(
                "launch_role_constraints.template.yaml.j2"
            ).render(
                portfolio={"DisplayName": self.portfolio,},
                portfolio_id=portfolio_id,
                launch_constraints=new_launch_constraints,
                product_name_to_id_dict=product_name_to_id_dict,
            )
            # time.sleep(30)
            stack_name_v1 = f"launch-constraints-for-portfolio-{portfolio_id}"
            cloudformation.ensure_deleted(StackName=stack_name_v1,)
            stack_name_v2 = f"launch-constraints-v2-for-portfolio-{portfolio_id}"
            cloudformation.create_or_update(
                StackName=stack_name_v2,
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
            )
            result = cloudformation.describe_stacks(StackName=stack_name_v2,).get(
                "Stacks"
            )[0]
            with self.output().open("w") as f:
                f.write(json.dumps(result, indent=4, default=str,))


class RequestPolicyTask(PortfolioManagementTask):
    type = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()
    organization = luigi.Parameter(default=None)

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
        }

    def run(self):
        if self.organization is not None:
            p = f"data/{self.type}/{self.region}/organizations/"
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)
            path = f"{p}/{self.organization}.json"
        else:
            p = f"data/{self.type}/{self.region}/accounts/"
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)
            path = f"{p}/{self.account_id}.json"

        f = open(path, "w")
        f.write(json.dumps(self.param_kwargs, indent=4, default=str,))
        f.close()
        self.write_output(self.param_kwargs)


class SharePortfolioTask(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_portfolio_access_single_page_{self.region}",
            f"servicecatalog.create_portfolio_share_{self.region}",
        ]

    def run(self):
        p = f"data/shares/{self.region}/{self.portfolio}/"
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        path = f"{p}/{self.account_id}.json"
        with open(path, "w") as f:
            f.write("{}")

        self.info(f"{self.uid}: checking {self.portfolio_id} with {self.account_id}")

        with betterboto_client.ClientContextManager(
            "servicecatalog", region_name=self.region
        ) as servicecatalog:
            account_ids = servicecatalog.list_portfolio_access_single_page(
                PortfolioId=self.portfolio_id, PageSize=20,
            ).get("AccountIds")

            if self.account_id in account_ids:
                self.info(
                    f"{self.uid}: not sharing {self.portfolio_id} with {self.account_id} as was previously shared"
                )
            else:
                self.info(
                    f"{self.uid}: sharing {self.portfolio_id} with {self.account_id}"
                )
                servicecatalog.create_portfolio_share(
                    PortfolioId=self.portfolio_id, AccountId=self.account_id,
                )
        self.write_output(self.param_kwargs)


class SharePortfolioViaOrgsTask(PortfolioManagementTask):
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    ou_to_share_with = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "ou_to_share_with": self.ou_to_share_with,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.create_portfolio_share",
            f"servicecatalog.describe_portfolio_share_status",
        ]

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.puppet_account_id),
            f"{self.puppet_account_id}-{self.region}-{config.get_puppet_role_name()}",
            region_name=self.region,
        ) as servicecatalog:
            portfolio_share_token = servicecatalog.create_portfolio_share(
                PortfolioId=self.portfolio_id,
                OrganizationNode=dict(
                    Type="ORGANIZATIONAL_UNIT", Value=self.ou_to_share_with
                ),
            ).get("PortfolioShareToken")

            status = "NOT_STARTED"

            while status in ["NOT_STARTED", "IN_PROGRESS"]:
                time.sleep(5)
                response = servicecatalog.describe_portfolio_share_status(
                    PortfolioShareToken=portfolio_share_token
                )
                status = response.get("Status")
                self.info(f"New status: {status}")

            if status in ["COMPLETED_WITH_ERRORS", "ERROR"]:
                errors = list()
                for error in response.get("ShareDetails").get("ShareErrors"):
                    if error.get("Error") == "DuplicateResourceException":
                        self.warning(yaml.safe_dump(error))
                    else:
                        errors.append(error)
                if len(errors) > 0:
                    raise Exception(yaml.safe_dump(response.get("ShareDetails")))

        self.write_output(self.param_kwargs)


class ShareAndAcceptPortfolioTask(
    PortfolioManagementTask, manifest_tasks.ManifestMixen
):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    sharing_mode = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
            "sharing_mode": self.sharing_mode,
        }

    def requires(self):

        if self.sharing_mode == constants.SHARING_MODE_AWS_ORGANIZATIONS:
            ou_to_share_with = self.manifest.get_account(self.account_id).get(
                "expanded_from"
            )
            if ou_to_share_with is None:
                self.warning(
                    f"Sharing {self.portfolio} with {self.account_id} not using orgs as there is no OU set for it"
                )
                return {
                    "share": SharePortfolioTask(
                        manifest_file_path=self.manifest_file_path,
                        portfolio=self.portfolio,
                        portfolio_id=self.portfolio_id,
                        account_id=self.account_id,
                        region=self.region,
                        puppet_account_id=self.puppet_account_id,
                    ),
                }
            else:
                return {
                    "share": SharePortfolioViaOrgsTask(
                        manifest_file_path=self.manifest_file_path,
                        portfolio=self.portfolio,
                        portfolio_id=self.portfolio_id,
                        region=self.region,
                        puppet_account_id=self.puppet_account_id,
                        ou_to_share_with=ou_to_share_with,
                    ),
                }

        else:
            return {
                "share": SharePortfolioTask(
                    manifest_file_path=self.manifest_file_path,
                    portfolio=self.portfolio,
                    portfolio_id=self.portfolio_id,
                    account_id=self.account_id,
                    region=self.region,
                    puppet_account_id=self.puppet_account_id,
                ),
            }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_accepted_portfolio_shares_single_page{self.account_id}_{self.region}",
            f"servicecatalog.accept_portfolio_share{self.account_id}_{self.region}",
            f"servicecatalog.associate_principal_with_portfolio{self.account_id}_{self.region}",
            f"servicecatalog.list_principals_for_portfolio{self.account_id}_{self.region}",
        ]

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}-{config.get_puppet_role_name()}",
            region_name=self.region,
        ) as cross_account_servicecatalog:
            was_accepted = False
            accepted_portfolio_shares = cross_account_servicecatalog.list_accepted_portfolio_shares_single_page().get(
                "PortfolioDetails"
            )
            for accepted_portfolio_share in accepted_portfolio_shares:
                if accepted_portfolio_share.get("Id") == self.portfolio_id:
                    was_accepted = True
                    break
            if not was_accepted:
                self.info(f"{self.uid}: accepting {self.portfolio_id}")
                cross_account_servicecatalog.accept_portfolio_share(
                    PortfolioId=self.portfolio_id,
                )

            principals_for_portfolio = cross_account_servicecatalog.list_principals_for_portfolio_single_page(
                PortfolioId=self.portfolio_id
            ).get(
                "Principals"
            )
            principal_was_associated = False
            principal_to_associate = config.get_puppet_role_arn(self.account_id)
            for principal_for_portfolio in principals_for_portfolio:
                if (
                    principal_for_portfolio.get("PrincipalARN")
                    == principal_to_associate
                ):
                    principal_was_associated = True

            if not principal_was_associated:
                cross_account_servicecatalog.associate_principal_with_portfolio(
                    PortfolioId=self.portfolio_id,
                    PrincipalARN=principal_to_associate,
                    PrincipalType="IAM",
                )

        self.write_output(self.param_kwargs)


class CreateAssociationsInPythonForPortfolioTask(PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.associate_principal_with_portfolio_{self.region}": 1,
        }

    def run(self):
        p = f"data/associations/{self.region}/{self.portfolio}/"
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        path = f"{p}/{self.account_id}.json"
        with open(path, "w") as f:
            f.write("{}")

        self.info(f"Creating the association for portfolio {self.portfolio_id}")
        with betterboto_client.ClientContextManager(
            "servicecatalog", region_name=self.region
        ) as servicecatalog:
            servicecatalog.associate_principal_with_portfolio(
                PortfolioId=self.portfolio_id,
                PrincipalARN=config.get_puppet_role_arn(self.account_id),
                PrincipalType="IAM",
            )
        self.write_output(self.param_kwargs)


class CreateShareForAccountLaunchRegion(PortfolioManagementTask):
    """for the given account_id and launch and region create the shares"""

    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    sharing_mode = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
            "sharing_mode": self.sharing_mode,
        }

    def requires(self):
        if self.account_id == self.puppet_account_id:
            return CreateAssociationsInPythonForPortfolioTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
            )
        else:
            return ShareAndAcceptPortfolioTask(
                manifest_file_path=self.manifest_file_path,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                puppet_account_id=self.puppet_account_id,
                sharing_mode=self.sharing_mode,
            )

    def run(self):
        self.write_output(self.param_kwargs)


class DisassociateProductFromPortfolio(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    product_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio_id": self.portfolio_id,
            "product_id": self.product_id,
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.disassociate_product_from_portfolio_{self.account_id}_{self.region}_{self.portfolio_id}_{self.product_id}": 1,
        }

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}-{config.get_puppet_role_name()}",
            region_name=self.region,
        ) as servicecatalog:
            results = servicecatalog.disassociate_product_from_portfolio(
                PortfolioId=self.portfolio_id, ProductId=self.product_id,
            )
            self.write_output(results)


class DisassociateProductsFromPortfolio(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio_id": self.portfolio_id,
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.search_products_as_admin_single_page_{self.account_id}_{self.region}_{self.portfolio_id}": 1,
        }

    def requires(self):
        disassociates = list()
        requirements = dict(disassociates=disassociates)
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}-{config.get_puppet_role_name()}",
            region_name=self.region,
        ) as servicecatalog:
            results = servicecatalog.search_products_as_admin_single_page(
                PortfolioId=self.portfolio_id
            )
            for product_view_detail in results.get("ProductViewDetails", []):
                disassociates.append(
                    DisassociateProductFromPortfolio(
                        account_id=self.account_id,
                        region=self.region,
                        portfolio_id=self.portfolio_id,
                        product_id=product_view_detail.get("ProductViewSummary").get(
                            "ProductId"
                        ),
                        manifest_file_path=self.manifest_file_path,
                    )
                )
        return requirements

    def run(self):
        self.write_output(self.params_for_results_display())


class DeleteLocalPortfolio(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio_id": self.portfolio_id,
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.delete_portfolio_{self.account_id}_{self.region}_{self.portfolio_id}": 1,
        }

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}-{config.get_puppet_role_name()}",
            region_name=self.region,
        ) as servicecatalog:
            servicecatalog.delete_portfolio(Id=self.portfolio_id)
            self.write_output(self.params_for_results_display())


class DeletePortfolioShare(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_accepted_portfolio_shares_single_page{self.account_id}_{self.region}",
            f"servicecatalog.delete_portfolio_share_{self.puppet_account_id}_{self.region}_{self.portfolio}",
        ]

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}-{config.get_puppet_role_name()}",
            region_name=self.region,
        ) as servicecatalog:
            self.info(
                f"About to delete the portfolio share for: {self.portfolio} account: {self.account_id}"
            )
            result = servicecatalog.list_accepted_portfolio_shares_single_page()
            portfolio_id = None
            for portfolio_detail in result.get("PortfolioDetails", []):
                if portfolio_detail.get("DisplayName") == self.portfolio:
                    portfolio_id = portfolio_detail.get("Id")
                    break
        if portfolio_id:
            with betterboto_client.CrossAccountClientContextManager(
                "servicecatalog",
                config.get_puppet_role_arn(self.puppet_account_id),
                f"{self.puppet_account_id}-{self.region}-{config.get_puppet_role_name()}",
                region_name=self.region,
            ) as servicecatalog:
                servicecatalog.delete_portfolio_share(
                    PortfolioId=portfolio_id, AccountId=self.account_id,
                )
        self.write_output(self.params_for_results_display())


class DeletePortfolio(PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    product_generation_method = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
        }

    def requires(self):
        requirements = list()
        is_puppet_account = self.account_id == self.puppet_account_id
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}-{config.get_puppet_role_name()}",
            region_name=self.region,
        ) as servicecatalog:
            result = None
            self.info("Checking portfolios for a match")
            response = servicecatalog.list_portfolios_single_page()
            for portfolio_detail in response.get("PortfolioDetails", []):
                if portfolio_detail.get("DisplayName") == self.portfolio:
                    result = portfolio_detail
                    self.info(f"Found a non-imported portfolio: {result}")
                    break
            if result:
                portfolio_id = result.get("Id")
                requirements.append(
                    general.DeleteCloudFormationStackTask(
                        account_id=self.account_id,
                        region=self.region,
                        stack_name=f"associations-for-portfolio-{portfolio_id}",
                    )
                )
                requirements.append(
                    general.DeleteCloudFormationStackTask(
                        account_id=self.account_id,
                        region=self.region,
                        stack_name=f"launch-constraints-v2-for-portfolio-{portfolio_id}",
                    )
                )
                if not is_puppet_account:
                    requirements.append(
                        DisassociateProductsFromPortfolio(
                            account_id=self.account_id,
                            region=self.region,
                            portfolio_id=portfolio_id,
                            manifest_file_path=self.manifest_file_path,
                        )
                    )
                    requirements.append(
                        DeleteLocalPortfolio(
                            account_id=self.account_id,
                            region=self.region,
                            portfolio_id=portfolio_id,
                            manifest_file_path=self.manifest_file_path,
                        )
                    )

            if not is_puppet_account:
                requirements.append(
                    DeletePortfolioShare(
                        account_id=self.account_id,
                        region=self.region,
                        portfolio=self.portfolio,
                        puppet_account_id=self.puppet_account_id,
                        manifest_file_path=self.manifest_file_path,
                    )
                )
        return requirements

    def run(self):
        self.write_output(self.params_for_results_display())


#
