import copy
import os
import re
import time
import traceback
from pathlib import Path

from betterboto import client as betterboto_client

from servicecatalog_puppet import aws, cli_command_helpers, constants

import luigi
import json

import logging

logger = logging.getLogger("tasks")


class PuppetTask(luigi.Task):

    @property
    def resources(self):
        resources_for_this_task = {}
        resource_parts = []
        if hasattr(self, 'region'):
            resource_parts.append(self.region)
        if hasattr(self, 'account_id'):
            resource_parts.append(self.account_id)

        if len(resource_parts) > 0:
            resources_for_this_task["_".join(resource_parts)] = 1

        return resources_for_this_task

    def params_for_results_display(self):
        return "Omitted"

    def write_output(self, content):
        with self.output().open('w') as f:
            f.write(
                json.dumps(
                    content,
                    indent=4,
                    default=str,
                )
            )


class GetSSMParamTask(PuppetTask):
    parameter_name = luigi.Parameter()
    name = luigi.Parameter()
    region = luigi.Parameter(default=None)

    def params_for_results_display(self):
        return {
            "parameter_name": self.parameter_name,
            "name": self.name,
            "region": self.region,
        }

    @property
    def uid(self):
        return f"{self.region}-{self.parameter_name}-{self.name}"

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.__class__.__name__}/"
            f"{self.uid}.json"
        )

    def run(self):
        with betterboto_client.ClientContextManager('ssm', region_name=self.region) as ssm:
            try:
                p = ssm.get_parameter(
                    Name=self.name,
                )
                self.write_output({
                    'Name': self.name,
                    'Region': self.region,
                    'Value': p.get('Parameter').get('Value')
                })
            except ssm.exceptions.ParameterNotFound as e:
                raise e


class GetVersionIdByVersionName(PuppetTask):
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/GetVersionIdByVersionName/"
            f"{self.account_id}-{self.region}-{self.portfolio}-{self.product}-{self.version}.json"
        )

    def requires(self):
        product_id = GetProductIdByProductName(
            self.portfolio,
            self.product,
            self.account_id,
            self.region,
        )
        return {
            'product': product_id,
        }

    def run(self):
        with self.input().get('product').open('r') as f:
            product_details = json.loads(f.read())
        version_id = None
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog',
                f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole",
                f"{self.account_id}-{self.region}",
                region_name=self.region
        ) as cross_account_servicecatalog:
            version_id = aws.get_version_id_for(
                cross_account_servicecatalog,
                product_details.get('product_id'),
                self.version
            )
            with self.output().open('w') as f:
                f.write(
                    json.dumps(
                        {
                            'version_name': self.version,
                            'version_id': version_id,
                        },
                        indent=4,
                        default=str,
                    )
                )


class GetProductIdByProductName(PuppetTask):
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
        }

    def requires(self):
        portfolio_id = GetPortfolioIdByPortfolioName(
            self.portfolio,
            self.account_id,
            self.region,
        )
        return {
            'portfolio': portfolio_id,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/GetProductIdByProductName/"
            f"{self.account_id}-{self.region}-{self.portfolio}-{self.product}.json"
        )

    def run(self):
        with self.input().get('portfolio').open('r') as f:
            portfolio_details = json.loads(f.read())
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog',
                f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole",
                f"{self.account_id}-{self.region}",
                region_name=self.region
        ) as cross_account_servicecatalog:
            product_id = aws.get_product_id_for(
                cross_account_servicecatalog,
                portfolio_details.get('portfolio_id'),
                self.product,
            )
            with self.output().open('w') as f:
                f.write(
                    json.dumps(
                        {
                            'product_name': self.product,
                            'product_id': product_id,
                        },
                        indent=4,
                        default=str,
                    )
                )


class GetPortfolioIdByPortfolioName(PuppetTask):
    portfolio = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/GetPortfolioIdByPortfolioName/"
            f"{self.account_id}-{self.region}-{self.portfolio}.json"
        )

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog',
                f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole",
                f"{self.account_id}-{self.region}",
                region_name=self.region
        ) as cross_account_servicecatalog:
            portfolio_id = aws.get_portfolio_id_for(cross_account_servicecatalog, self.portfolio)
            with self.output().open('w') as f:
                f.write(
                    json.dumps(
                        {
                            "portfolio_name": self.portfolio,
                            "portfolio_id": portfolio_id,
                        },
                        indent=4,
                        default=str,
                    )
                )


class ProvisionProductTask(PuppetTask):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    parameters = luigi.ListParameter(default=[], significant=False)
    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    dependencies = luigi.ListParameter(default=[], significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    should_use_sns = luigi.Parameter(significant=False, default=False)
    requested_priority = luigi.Parameter(significant=False, default=0)

    try_count = 1

    @property
    def uid(self):
        return f"{self.launch_name}-{self.account_id}-{self.region}-{self.portfolio}-{self.product}-{self.version}"

    @property
    def priority(self):
        return self.requested_priority

    def requires(self):
        ssm_params = {}
        for param_input in self.ssm_param_inputs:
            ssm_params[param_input.get('parameter_name')] = GetSSMParamTask(**param_input)
        dependencies = []
        version_id = GetVersionIdByVersionName(
            self.portfolio,
            self.product,
            self.version,
            self.account_id,
            self.region,
        )
        product_id = GetProductIdByProductName(
            self.portfolio,
            self.product,
            self.account_id,
            self.region,
        )
        for r in self.dependencies:
            if r.get('status') is not None:
                if r.get('status') == constants.TERMINATED:
                    raise Exception("Unsupported")
                new_r = r.get_wrapped()
                del new_r['status']
                dependencies.append(
                    self.__class__(**new_r)
                )
            else:
                dependencies.append(
                    self.__class__(**r)
                )
        return {
            'dependencies': dependencies,
            'ssm_params': ssm_params,
            'version': version_id,
            'product': product_id,
        }

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/ProvisionProductTask/"
            f"{self.uid}.json"
        )

    def run(self):
        logger.info(f"[{self.uid}] starting deploy try {self.try_count} of {self.retry_count}")

        with self.input().get('version').open('r') as f:
            version_id = json.loads(f.read()).get('version_id')
        with self.input().get('product').open('r') as f:
            product_id = json.loads(f.read()).get('product_id')

        all_params = {}

        logger.info(f"[{self.uid}] :: collecting ssm params")
        for ssm_param_name, ssm_param in self.input().get('ssm_params', {}).items():
            with ssm_param.open('r') as f:
                all_params[ssm_param_name] = f.read()

        logger.info(f"[{self.uid}] collecting manifest params")
        for parameter in self.parameters:
            all_params[parameter.get('name')] = parameter.get('value')

        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.region}-{self.account_id}', region_name=self.region
        ) as service_catalog:
            logger.info(f"[{self.uid}] looking for previous failures")
            path_id = aws.get_path_for_product(service_catalog, product_id, self.portfolio)

            provisioned_product_id, provisioning_artifact_id = aws.terminate_if_status_is_not_available(
                service_catalog, self.launch_name, product_id, self.account_id, self.region
            )
            logger.info(f"[{self.uid}] pp_id: {provisioned_product_id}, paid : {provisioning_artifact_id}")

            with betterboto_client.CrossAccountClientContextManager(
                    'cloudformation', role, f'cfn-{self.region}-{self.account_id}', region_name=self.region
            ) as cloudformation:
                need_to_provision = True
                if provisioned_product_id:
                    default_cfn_params = aws.get_default_parameters_for_stack(
                        cloudformation, f"SC-{self.account_id}-{provisioned_product_id}"
                    )
                else:
                    default_cfn_params = {}

                logging.info(
                    f"running as {role},checking {product_id} {version_id} {path_id} in {self.account_id} {self.region}"
                )
                provisioning_artifact_parameters = service_catalog.describe_provisioning_parameters(
                    ProductId=product_id, ProvisioningArtifactId=version_id, PathId=path_id,
                ).get('ProvisioningArtifactParameters', [])
                new_version_param_names = [p.get('ParameterKey') for p in provisioning_artifact_parameters]

                for default_cfn_param_name in default_cfn_params.keys():
                    if all_params.get(default_cfn_param_name) is None:
                        if default_cfn_params.get(default_cfn_param_name) is not None:
                            if default_cfn_param_name in new_version_param_names:
                                all_params[default_cfn_param_name] = default_cfn_params[default_cfn_param_name]

                if provisioning_artifact_id == version_id:
                    logger.info(
                        f"[{self.uid}] found previous good provision")
                    if provisioned_product_id:
                        logger.info(
                            f"[{self.uid}] checking params for diffs")
                        provisioned_parameters = aws.get_parameters_for_stack(
                            cloudformation,
                            f"SC-{self.account_id}-{provisioned_product_id}"
                        )
                        logger.info(f"[{self.uid}] current params: {provisioned_parameters}")

                        logger.info(f"[{self.uid}] new params: {all_params}")

                        if provisioned_parameters == all_params:
                            logger.info(f"[{self.uid}] params unchanged")
                            need_to_provision = False
                        else:
                            logger.info(f"[{self.uid}] params changed")

                if need_to_provision:
                    logger.info(f"[{self.uid}] about to provision with params: {json.dumps(all_params)}")

                    if provisioned_product_id:
                        with betterboto_client.CrossAccountClientContextManager(
                                'cloudformation', role, f'cfn-{self.region}-{self.account_id}', region_name=self.region
                        ) as cloudformation:
                            stack = aws.get_stack_output_for(
                                cloudformation,
                                f"SC-{self.account_id}-{provisioned_product_id}"
                            )
                            stack_status = stack.get('StackStatus')
                            logger.info(
                                f"[{self.uid}] current cfn stack_status is {stack_status}")
                            if stack_status not in ["UPDATE_COMPLETE", "CREATE_COMPLETE"]:
                                raise Exception(
                                    f"[{self.uid}] current cfn stack_status is {stack_status}"
                                )

                    provisioned_product_id = aws.provision_product(
                        service_catalog,
                        self.launch_name,
                        self.account_id,
                        self.region,
                        product_id,
                        version_id,
                        self.puppet_account_id,
                        path_id,
                        all_params,
                        self.version,
                        self.should_use_sns,
                    )

                with betterboto_client.CrossAccountClientContextManager(
                        'cloudformation', role, f'cfn-{self.region}-{self.account_id}', region_name=self.region
                ) as spoke_cloudformation:
                    stack_details = aws.get_stack_output_for(
                        spoke_cloudformation, f"SC-{self.account_id}-{provisioned_product_id}"
                    )

                for ssm_param_output in self.ssm_param_outputs:
                    logger.info(f"[{self.uid}] writing SSM Param: {ssm_param_output.get('stack_output')}")
                    with betterboto_client.ClientContextManager('ssm') as ssm:
                        found_match = False
                        for output in stack_details.get('Outputs', []):
                            if output.get('OutputKey') == ssm_param_output.get('stack_output'):
                                found_match = True
                                logger.info(f"[{self.uid}] found value")
                                ssm.put_parameter(
                                    Name=ssm_param_output.get('param_name'),
                                    Value=output.get('OutputValue'),
                                    Type=ssm_param_output.get('param_type', 'String'),
                                    Overwrite=True,
                                )
                        if not found_match:
                            raise Exception(
                                f"[{self.uid}] Could not find match for {ssm_param_output.get('stack_output')}"
                            )

                with self.output().open('w') as f:
                    f.write(
                        json.dumps(
                            stack_details,
                            indent=4,
                            default=str,
                        )
                    )
                logger.info(f"[{self.uid}] finished provisioning")


class ProvisionProductDryRunTask(PuppetTask):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])
    dependencies = luigi.ListParameter(default=[])

    retry_count = luigi.IntParameter(default=1)

    worker_timeout = luigi.IntParameter(default=0, significant=False)

    ssm_param_outputs = luigi.ListParameter(default=[])

    try_count = 1

    def requires(self):
        version_id = GetVersionIdByVersionName(
            self.portfolio,
            self.product,
            self.version,
            self.account_id,
            self.region,
        )
        product_id = GetProductIdByProductName(
            self.portfolio,
            self.product,
            self.account_id,
            self.region,
        )
        dependencies = []
        for r in self.dependencies:
            if r.get('status') is not None:
                if r.get('status') == constants.TERMINATED:
                    raise Exception("Unsupported")
                new_r = r.get_wrapped()
                del new_r['status']
                dependencies.append(
                    self.__class__(**new_r)
                )
            else:
                dependencies.append(
                    self.__class__(**r)
                )
        return {
            'dependencies': dependencies,
            'version': version_id,
            'product': product_id,
        }

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/ProvisionProductDryRunTask/"
            f"{self.launch_name}-{self.account_id}-{self.region}-{self.portfolio}-{self.product}-{self.version}.json"
        )

    def run(self):
        logger_prefix = f"[{self.launch_name}] {self.account_id}:{self.region}"
        logger.info(
            f"{logger_prefix} :: starting dryrun of {self.retry_count}"
        )

        with self.input().get('version').open('r') as f:
            version_id = json.loads(f.read()).get('version_id')

        with self.input().get('product').open('r') as f:
            product_id = json.loads(f.read()).get('product_id')

        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.region}-{self.account_id}', region_name=self.region
        ) as service_catalog:
            logger.info(f"{logger_prefix} :: looking for previous failures")

            response = service_catalog.search_provisioned_products(
                Filters={'SearchQuery': [
                    "productId:{}".format(product_id)
                ]}
            )
            provisioning_artifact_id = False
            for r in response.get('ProvisionedProducts', []):
                if r.get('Name') == self.launch_name:
                    current_status = r.get('Status')
                    if current_status in ["AVAILABLE", "TAINTED"]:
                        provisioned_product_id = r.get('Id')
                        provisioning_artifact_id = r.get('ProvisioningArtifactId')

                        if provisioning_artifact_id != version_id:
                            self.write_result(
                                current_version=self.get_current_version(provisioning_artifact_id, service_catalog),
                                new_version=self.version,
                                effect=constants.CHANGE,
                                notes='Version change',
                            )
                            return
                        else:
                            all_params = {}
                            logger.info(f"{logger_prefix} :: collecting ssm params")
                            for ssm_param_name, ssm_param in self.input().get('ssm_params', {}).items():
                                all_params[ssm_param_name] = ssm_param.read()
                            logger.info(f"{logger_prefix} :: collecting manifest params")
                            for parameter in self.parameters:
                                all_params[parameter.get('name')] = parameter.get('value')

                            with betterboto_client.CrossAccountClientContextManager(
                                    'cloudformation', role, f'cfn-{self.region}-{self.account_id}',
                                    region_name=self.region
                            ) as cloudformation:
                                default_cfn_params = aws.get_default_parameters_for_stack(
                                    cloudformation, f"SC-{self.account_id}-{provisioned_product_id}"
                                )

                            for default_cfn_param_name in default_cfn_params.keys():
                                if all_params.get(default_cfn_param_name) is None:
                                    all_params[default_cfn_param_name] = default_cfn_params[default_cfn_param_name]

                            logger.info(
                                f"{logger_prefix} :: found previous good provision"
                            )
                            if provisioned_product_id:
                                logger.info(
                                    f"{logger_prefix} :: checking params for diffs"
                                )
                                provisioned_parameters = aws.get_parameters_for_stack(
                                    cloudformation,
                                    f"SC-{self.account_id}-{provisioned_product_id}"
                                )
                                logger.info(f"{logger_prefix} :: "
                                            f"current params: {provisioned_parameters}")

                                logger.info(f"{logger_prefix} :: "
                                            f"new params: {all_params}")

                                if provisioned_parameters == all_params:
                                    logger.info(f"{logger_prefix} :: params unchanged")
                                    self.write_result(
                                        current_version=self.version,
                                        new_version=self.version,
                                        effect=constants.NO_CHANGE,
                                        notes="Versions and params are the same",
                                    )
                                    return
                                else:
                                    logger.info(f"{logger_prefix} :: params changed")
                                    self.write_result(
                                        current_version=self.version,
                                        new_version=self.version,
                                        effect=constants.CHANGE,
                                        notes="Versions are the same but the params are different",
                                    )
                                    return

                    else:
                        current_version = self.get_current_version(provisioning_artifact_id, service_catalog)

                        if current_status in ["UNDER_CHANGE", "PLAN_IN_PROGRESS"]:
                            self.write_result(
                                current_version=current_version,
                                new_version=current_version,
                                effect=constants.NO_CHANGE,
                                notes=f"provisioned product status was {current_status}"
                            )
                            return

                        elif current_status == 'ERROR':
                            self.write_result(
                                current_version=current_version,
                                new_version=self.version,
                                effect=constants.CHANGE,
                                notes=f"provisioned product status was {current_status}"
                            )
                            return

            logger.info(f"{logger_prefix} no version of product has not been provisioned")
            self.write_result(
                current_version=None,
                effect=constants.CHANGE,
                new_version=self.version,
                notes="Fresh install",
            )

    def get_current_version(self, provisioning_artifact_id, service_catalog):
        with self.input().get('product').open('r') as f:
            product_id = json.loads(f.read()).get('product_id')

        return service_catalog.describe_provisioning_artifact(
            ProvisioningArtifactId=provisioning_artifact_id,
            ProductId=product_id,
        ).get('ProvisioningArtifactDetail').get('Name')

    def write_result(self, current_version, new_version, effect, notes=''):
        with self.output().open('w') as f:
            f.write(
                json.dumps(
                    {
                        "current_version": current_version,
                        "new_version": new_version,
                        "effect": effect,
                        "notes": notes,
                        "params": self.param_kwargs
                    },
                    indent=4,
                    default=str,
                )
            )


class TerminateProductTask(PuppetTask):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    retry_count = luigi.IntParameter(default=1)

    ssm_param_outputs = luigi.ListParameter(default=[])

    worker_timeout = luigi.IntParameter(default=0, significant=False)

    try_count = 1

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])
    dependencies = luigi.ListParameter(default=[])

    def requires(self):
        product_id = GetProductIdByProductName(
            self.portfolio,
            self.product,
            self.account_id,
            self.region,
        )
        return {
            'product': product_id,
        }

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/TerminateProductTask/"
            f"{self.account_id}-{self.region}-{self.portfolio}-{self.product}-{self.version}.json"
        )

    def run(self):
        logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: "
                    f"starting terminate try {self.try_count} of {self.retry_count}")

        with self.input().get('product').open('r') as f:
            product_id = json.loads(f.read()).get('product_id')
        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.region}-{self.account_id}', region_name=self.region
        ) as service_catalog:
            logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: looking for previous failures")
            provisioned_product_id, provisioning_artifact_id = aws.ensure_is_terminated(
                service_catalog, self.launch_name, product_id
            )
            log_output = self.to_str_params()
            log_output.update({
                "provisioned_product_id": provisioned_product_id,
            })

            for ssm_param_output in self.ssm_param_outputs:
                param_name = ssm_param_output.get('param_name')
                logger.info(
                    f"[{self.launch_name}] {self.account_id}:{self.region} :: deleting SSM Param: {param_name}"
                )
                with betterboto_client.ClientContextManager('ssm') as ssm:
                    try:
                        ssm.delete_parameter(
                            Name=param_name,
                        )
                        logger.info(
                            f"[{self.launch_name}] {self.account_id}:{self.region} :: deleting SSM Param: {param_name}"
                        )
                    except ssm.exceptions.ParameterNotFound:
                        logger.info(
                            f"[{self.launch_name}] {self.account_id}:{self.region} :: SSM Param: {param_name} not found"
                        )

            with self.output().open('w') as f:
                f.write(
                    json.dumps(
                        log_output,
                        indent=4,
                        default=str,
                    )
                )

            logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: finished terminating")


class TerminateProductDryRunTask(PuppetTask):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    retry_count = luigi.IntParameter(default=1)

    ssm_param_outputs = luigi.ListParameter(default=[])

    worker_timeout = luigi.IntParameter(default=0, significant=False)

    try_count = 1

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])
    dependencies = luigi.ListParameter(default=[])

    def requires(self):
        product_id = GetProductIdByProductName(
            self.portfolio,
            self.product,
            self.account_id,
            self.region,
        )
        return {
            'product': product_id,
        }

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/TerminateProductDryRunTask/"
            f"{self.launch_name}-{self.account_id}-{self.region}-{self.portfolio}-{self.product}-{self.version}.json"
        )

    def write_result(self, current_version, new_version, effect, notes=''):
        with self.output().open('w') as f:
            f.write(
                json.dumps(
                    {
                        "current_version": current_version,
                        "new_version": new_version,
                        "effect": effect,
                        "notes": notes,
                        "params": self.param_kwargs
                    },
                    indent=4,
                    default=str,
                )
            )

    def run(self):
        logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: "
                    f"starting dry run terminate try {self.try_count} of {self.retry_count}")

        with self.input().get('product').open('r') as f:
            product_id = json.loads(f.read()).get('product_id')

        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.region}-{self.account_id}', region_name=self.region
        ) as service_catalog:
            logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: looking for previous failures")
            r = aws.get_provisioned_product_details(product_id, self.launch_name, service_catalog)

            if r is None:
                self.write_result(
                    '-', '-', constants.NO_CHANGE, notes='There is nothing to terminate'
                )
            else:
                provisioned_product_name = service_catalog.describe_provisioning_artifact(
                    ProvisioningArtifactId=r.get('ProvisioningArtifactId'),
                    ProductId=product_id,
                ).get('ProvisioningArtifactDetail').get('Name')

                if r.get('Status') != "TERMINATED":
                    self.write_result(
                        provisioned_product_name, '-', constants.CHANGE, notes='The product would be terminated'
                    )
                else:
                    self.write_result(
                        '-', '-', constants.CHANGE, notes='The product is already terminated'
                    )


class CreateSpokeLocalPortfolioTask(PuppetTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()

    provider_name = luigi.Parameter(significant=False, default='not set')
    description = luigi.Parameter(significant=False, default='not set')

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/CreateSpokeLocalPortfolioTask/"
            f"{self.account_id}-{self.region}-{self.portfolio}.json"
        )

    def run(self):
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: starting creating portfolio")
        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.account_id}-{self.region}', region_name=self.region
        ) as spoke_service_catalog:
            spoke_portfolio = aws.ensure_portfolio(
                spoke_service_catalog,
                self.portfolio,
                self.provider_name,
                self.description,
            )
        with self.output().open('w') as f:
            f.write(
                json.dumps(
                    spoke_portfolio,
                    indent=4,
                    default=str,
                )
            )
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: finished creating portfolio")


class CreateAssociationsForPortfolioTask(PuppetTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    associations = luigi.ListParameter(default=[])
    dependencies = luigi.ListParameter(default=[])

    should_use_sns = luigi.Parameter(significant=False, default=False)

    def requires(self):
        return {
            'create_spoke_local_portfolio_task': CreateSpokeLocalPortfolioTask(
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
            ),
            'deps': [ProvisionProductTask(**dependency) for dependency in self.dependencies]
        }

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/CreateAssociationsForPortfolioTask/"
            f"{self.account_id}-{self.region}-{self.portfolio}.json"
        )

    def run(self):
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: starting creating associations")
        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"

        with self.input().get('create_spoke_local_portfolio_task').open('r') as f:
            portfolio_id = json.loads(f.read()).get('Id')
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: using portfolio_id: {portfolio_id}")

        with betterboto_client.CrossAccountClientContextManager(
                'cloudformation', role, f'cfn-{self.account_id}-{self.region}', region_name=self.region
        ) as cloudformation:
            template = cli_command_helpers.env.get_template('associations.template.yaml.j2').render(
                portfolio={
                    'DisplayName': self.portfolio,
                    'Associations': self.associations
                },
                portfolio_id=portfolio_id,
            )
            stack_name = f"associations-for-portfolio-{portfolio_id}"
            cloudformation.create_or_update(
                StackName=stack_name,
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:aws:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ] if self.should_use_sns else [],
            )
            result = cloudformation.describe_stacks(
                StackName=stack_name,
            ).get('Stacks')[0]
            with self.output().open('w') as f:
                f.write(
                    json.dumps(
                        result,
                        indent=4,
                        default=str,
                    )
                )
            logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: Finished importing")


class ImportIntoSpokeLocalPortfolioTask(PuppetTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()

    hub_portfolio_id = luigi.Parameter()

    def requires(self):
        return CreateSpokeLocalPortfolioTask(
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
        )

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "hub_portfolio_id": self.hub_portfolio_id,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/ImportIntoSpokeLocalPortfolioTask/"
            f"{self.account_id}-{self.region}-{self.portfolio}-{self.hub_portfolio_id}.json"
        )

    def run(self):
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: starting to import into spoke")

        product_name_to_id_dict = {}

        with betterboto_client.ClientContextManager(
                'servicecatalog', region_name=self.region
        ) as service_catalog:
            response = service_catalog.search_products_as_admin_single_page(PortfolioId=self.hub_portfolio_id)
            for product_view_detail in response.get('ProductViewDetails', []):
                spoke_product_id = False
                target_product_id = False
                product_view_summary = product_view_detail.get('ProductViewSummary')
                hub_product_name = product_view_summary.get('Name')
                hub_product_id = product_view_summary.get('ProductId')

                product_versions_that_should_be_copied = {}
                product_versions_that_should_be_updated = {}
                hub_provisioning_artifact_details = service_catalog.list_provisioning_artifacts(
                    ProductId=hub_product_id
                ).get('ProvisioningArtifactDetails', [])
                for hub_provisioning_artifact_detail in hub_provisioning_artifact_details:
                    if hub_provisioning_artifact_detail.get('Type') == 'CLOUD_FORMATION_TEMPLATE':
                        product_versions_that_should_be_copied[
                            f"{hub_provisioning_artifact_detail.get('Name')}"
                        ] = hub_provisioning_artifact_detail
                        product_versions_that_should_be_updated[
                            f"{hub_provisioning_artifact_detail.get('Name')}"
                        ] = hub_provisioning_artifact_detail

                logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: Copying {hub_product_name}")
                hub_product_arn = product_view_detail.get('ProductARN')
                copy_args = {
                    'SourceProductArn': hub_product_arn,
                    'CopyOptions': [
                        'CopyTags',
                    ],
                }
                with self.input().open('r') as f:
                    spoke_portfolio = json.loads(f.read())
                portfolio_id = spoke_portfolio.get("Id")

                logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} {hub_product_name} :: searching in "
                            f"spoke for product")
                role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
                with betterboto_client.CrossAccountClientContextManager(
                        'servicecatalog', role, f"sc-{self.account_id}-{self.region}", region_name=self.region
                ) as spoke_service_catalog:
                    p = None
                    try:
                        p = spoke_service_catalog.search_products_as_admin_single_page(
                            PortfolioId=portfolio_id,
                            Filters={'FullTextSearch': [hub_product_name]}
                        )
                    except spoke_service_catalog.exceptions.ResourceNotFoundException as e:
                        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} {hub_product_name} :: "
                                    f"swallowing exception: {str(e)}")

                    if p is not None:
                        for spoke_product_view_details in p.get('ProductViewDetails'):
                            spoke_product_view = spoke_product_view_details.get('ProductViewSummary')
                            if spoke_product_view.get('Name') == hub_product_name:
                                spoke_product_id = spoke_product_view.get('ProductId')
                                copy_args['TargetProductId'] = spoke_product_id
                                spoke_provisioning_artifact_details = spoke_service_catalog.list_provisioning_artifacts(
                                    ProductId=spoke_product_id
                                ).get('ProvisioningArtifactDetails')
                                for provisioning_artifact_detail in spoke_provisioning_artifact_details:
                                    id_to_delete = f"{provisioning_artifact_detail.get('Name')}"
                                    if product_versions_that_should_be_copied.get(id_to_delete, None) is not None:
                                        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} "
                                                    f"{hub_product_name} :: Going to skip "
                                                    f"{spoke_product_id} "
                                                    f"{provisioning_artifact_detail.get('Name')}"
                                                    )
                                        del product_versions_that_should_be_copied[id_to_delete]

                    if len(product_versions_that_should_be_copied.keys()) == 0:
                        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} {hub_product_name} :: "
                                    f"no versions to copy")
                    else:
                        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} {hub_product_name} :: "
                                    f"about to copy product")

                        copy_args['SourceProvisioningArtifactIdentifiers'] = [
                            {'Id': a.get('Id')} for a in product_versions_that_should_be_copied.values()
                        ]

                        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: about to copy product with"
                                    f"args: {copy_args}")
                        copy_product_token = spoke_service_catalog.copy_product(
                            **copy_args
                        ).get('CopyProductToken')
                        target_product_id = None
                        while True:
                            time.sleep(5)
                            r = spoke_service_catalog.describe_copy_product_status(
                                CopyProductToken=copy_product_token
                            )
                            target_product_id = r.get('TargetProductId')
                            logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: "
                                        f"{hub_product_name} status: {r.get('CopyProductStatus')}")
                            if r.get('CopyProductStatus') == 'FAILED':
                                raise Exception(f"[{self.portfolio}] {self.account_id}:{self.region} :: Copying "
                                                f"{hub_product_name} failed: {r.get('StatusDetail')}")
                            elif r.get('CopyProductStatus') == 'SUCCEEDED':
                                break

                        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: adding {target_product_id} "
                                    f"to portfolio {portfolio_id}")
                        spoke_service_catalog.associate_product_with_portfolio(
                            ProductId=target_product_id,
                            PortfolioId=portfolio_id,
                        )

                        # associate_product_with_portfolio is not a synchronous request
                        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: waiting for adding of "
                                    f"{target_product_id} to portfolio {portfolio_id}")
                        while True:
                            time.sleep(2)
                            response = spoke_service_catalog.search_products_as_admin_single_page(
                                PortfolioId=portfolio_id,
                            )
                            products_ids = [
                                product_view_detail.get('ProductViewSummary').get('ProductId') for product_view_detail
                                in response.get('ProductViewDetails')
                            ]
                            logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: Looking for "
                                        f"{target_product_id} in {products_ids}")

                            if target_product_id in products_ids:
                                break

                        product_name_to_id_dict[hub_product_name] = target_product_id

                    product_id_in_spoke = spoke_product_id or target_product_id
                    spoke_provisioning_artifact_details = spoke_service_catalog.list_provisioning_artifacts(
                        ProductId=product_id_in_spoke
                    ).get('ProvisioningArtifactDetails', [])
                    for version_name, version_details in product_versions_that_should_be_updated.items():
                        logging.info(f"{version_name} is active: {version_details.get('Active')} in hub")
                        for spoke_provisioning_artifact_detail in spoke_provisioning_artifact_details:
                            if spoke_provisioning_artifact_detail.get('Name') == version_name:
                                logging.info(
                                    f"Updating active of {version_name}/{spoke_provisioning_artifact_detail.get('Id')} "
                                    f"in the spoke to {version_details.get('Active')}"
                                )
                                spoke_service_catalog.update_provisioning_artifact(
                                    ProductId=product_id_in_spoke,
                                    ProvisioningArtifactId=spoke_provisioning_artifact_detail.get('Id'),
                                    Active=version_details.get('Active'),
                                )

        with self.output().open('w') as f:
            f.write(
                json.dumps(
                    {
                        'portfolio': spoke_portfolio,
                        'product_versions_that_should_be_copied': product_versions_that_should_be_copied,
                        'products': product_name_to_id_dict,
                    },
                    indent=4,
                    default=str,
                )
            )
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: Finished importing")


class CreateLaunchRoleConstraintsForPortfolio(PuppetTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    hub_portfolio_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    launch_constraints = luigi.DictParameter()

    dependencies = luigi.ListParameter(default=[])

    should_use_sns = luigi.Parameter(default=False, significant=False)

    def requires(self):
        return {
            'create_spoke_local_portfolio_task': ImportIntoSpokeLocalPortfolioTask(
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                hub_portfolio_id=self.hub_portfolio_id,
            ),
            'deps': [ProvisionProductTask(**dependency) for dependency in self.dependencies]
        }

    def run(self):
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: Creating launch role constraints for "
                    f"{self.hub_portfolio_id}")
        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with self.input().get('create_spoke_local_portfolio_task').open('r') as f:
            dependency_output = json.loads(f.read())
        spoke_portfolio = dependency_output.get('portfolio')
        portfolio_id = spoke_portfolio.get('Id')
        product_name_to_id_dict = dependency_output.get('products')
        with betterboto_client.CrossAccountClientContextManager(
                'cloudformation', role, f'cfn-{self.account_id}-{self.region}', region_name=self.region
        ) as cloudformation:
            new_launch_constraints = []
            for launch_constraint in self.launch_constraints:
                new_launch_constraint = {
                    'products': [],
                    'roles': launch_constraint.get('roles')
                }
                if launch_constraint.get('products', None) is not None:
                    if isinstance(launch_constraint.get('products'), tuple):
                        new_launch_constraint['products'] += launch_constraint.get('products')
                    elif isinstance(launch_constraint.get('products'), str):
                        with betterboto_client.CrossAccountClientContextManager(
                                'servicecatalog', role, f'sc-{self.account_id}-{self.region}', region_name=self.region
                        ) as service_catalog:
                            response = service_catalog.search_products_as_admin_single_page(PortfolioId=portfolio_id)
                            for product_view_details in response.get('ProductViewDetails', []):
                                product_view_summary = product_view_details.get('ProductViewSummary')
                                product_name_to_id_dict[product_view_summary.get('Name')] = product_view_summary.get(
                                    'ProductId')
                                if re.match(launch_constraint.get('products'), product_view_summary.get('Name')):
                                    new_launch_constraint['products'].append(product_view_summary.get('Name'))

                if launch_constraint.get('product', None) is not None:
                    new_launch_constraint['products'].append(launch_constraint.get('product'))

                new_launch_constraints.append(new_launch_constraint)

            template = cli_command_helpers.env.get_template('launch_role_constraints.template.yaml.j2').render(
                portfolio={
                    'DisplayName': self.portfolio,
                },
                portfolio_id=portfolio_id,
                launch_constraints=new_launch_constraints,
                product_name_to_id_dict=product_name_to_id_dict,
            )
            time.sleep(30)
            stack_name_v1 = f"launch-constraints-for-portfolio-{portfolio_id}"
            cloudformation.ensure_deleted(
                StackName=stack_name_v1,
            )
            stack_name_v2 = f"launch-constraints-v2-for-portfolio-{portfolio_id}"
            cloudformation.create_or_update(
                StackName=stack_name_v2,
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:aws:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ] if self.should_use_sns else [],
            )
            result = cloudformation.describe_stacks(
                StackName=stack_name_v2,
            ).get('Stacks')[0]
            with self.output().open('w') as f:
                f.write(
                    json.dumps(
                        result,
                        indent=4,
                        default=str,
                    )
                )

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "hub_portfolio_id": self.hub_portfolio_id,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/CreateLaunchRoleConstraintsForPortfolio/"
            f"{self.account_id}-{self.region}-{self.portfolio}-{self.hub_portfolio_id}.json"
        )


class ResetProvisionedProductOwnerTask(PuppetTask):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()

    product_id = luigi.Parameter()
    version_id = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])
    dependencies = luigi.ListParameter(default=[])

    retry_count = luigi.IntParameter(default=1)

    worker_timeout = luigi.IntParameter(default=0, significant=False)

    ssm_param_outputs = luigi.ListParameter(default=[])

    try_count = 1

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/ResetProvisionedProductOwnerTask/"
            f"{self.launch_name}-{self.account_id}-{self.region}-{self.portfolio}-{self.product}-{self.version}.json"
        )

    def run(self):
        logger_prefix = f"[{self.launch_name}] {self.account_id}:{self.region}"
        logger.info(
            f"{logger_prefix} :: starting ResetProvisionedProductOwnerTask of {self.retry_count}"
        )

        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.region}-{self.account_id}', region_name=self.region
        ) as service_catalog:
            logger.info(
                f"[{logger_prefix} :: Checking if existing provisioned product exists"
            )
            provisioned_product_search_result = service_catalog.search_provisioned_products(
                AccessLevelFilter={
                    'Key': 'Account',
                    'Value': 'self'
                },
                Filters={
                    'SearchQuery': [
                        f'name:{self.launch_name}',
                    ]
                }
            ).get('ProvisionedProducts', [])
            if provisioned_product_search_result:
                provisioned_product_id = provisioned_product_search_result[0].get('Id')
                logger.info(f"[{logger_prefix} :: Ensuring current provisioned product owner is correct")
                service_catalog.update_provisioned_product_properties(
                    ProvisionedProductId=provisioned_product_id,
                    ProvisionedProductProperties={
                        'OWNER': f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
                    }
                )


class RequestPolicyTask(PuppetTask):
    type = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()
    organization = luigi.Parameter(default=None)

    @property
    def uid(self):
        return f"{self.__class__.__name__}/{self.account_id}--{self.region}"

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.uid}.json"
        )

    def run(self):
        if self.organization is not None:
            p = f'data/{self.type}/{self.region}/organizations/'
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)
            path = f'{p}/{self.organization}.json'
        else:
            p = f'data/{self.type}/{self.region}/accounts/'
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)
            path = f'{p}/{self.account_id}.json'

        f = open(path, 'w')
        f.write(
            json.dumps(
                self.param_kwargs,
                indent=4,
                default=str,
            )
        )
        f.close()
        self.write_output(self.param_kwargs)


class ShareAndAcceptPortfolioTask(PuppetTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    @property
    def uid(self):
        return f"{self.__class__.__name__}/{self.account_id}--{self.region}--{self.portfolio}"

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.uid}.json"
        )

    def run(self):
        logger.info(f"{self.uid} starting ShareAndAcceptPortfolioTask")
        portfolio_id = aws.get_portfolio_for(self.portfolio, self.puppet_account_id, self.region).get('Id')
        p = f'data/shares/{self.region}/{self.portfolio}/'
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        path = f'{p}/{self.account_id}.json'
        with open(path, 'w') as f:
            f.write("{}")

        with betterboto_client.ClientContextManager('servicecatalog', region_name=self.region) as servicecatalog:
            logging.info(f"{self.uid}: sharing {portfolio_id} with {self.account_id}")
            r = servicecatalog.create_portfolio_share(
                PortfolioId=portfolio_id,
                AccountId=self.account_id,
            )
            portfolio_share_token = r.get('PortfolioShareToken')

            logging.info(f"{self.uid}: pmd {r}")
            logging.info(f"{self.uid}: received {portfolio_share_token}")

            status = "IN_PROGRESS"
            # while status not in ['COMPLETED', 'COMPLETED_WITH_ERRORS', 'ERROR']:
            #     status = servicecatalog.describe_portfolio_share_status(
            #         PortfolioShareToken=portfolio_share_token
            #     ).get('Status')
            #     logging.info(f"{self.uid}: status is {status}")

            status = "COMPLETED"
            if status == 'COMPLETED':
                logging.info(f"{self.uid}: status is {status}")
                with betterboto_client.CrossAccountClientContextManager(
                        'servicecatalog',
                        f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole",
                        f"{self.account_id}-{self.region}-PuppetRole",
                        region_name=self.region,
                ) as cross_account_servicecatalog:
                    logging.info(f"{self.uid}: accepting {portfolio_id}")
                    cross_account_servicecatalog.accept_portfolio_share(
                        PortfolioId=portfolio_id,
                    )
                    cross_account_servicecatalog.associate_principal_with_portfolio(
                        PortfolioId=portfolio_id,
                        PrincipalARN=f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole",
                        PrincipalType='IAM',
                    )
            else:
                raise Exception(f"{self.uid}: Sharing not completed: {status}")
        self.write_output(self.param_kwargs)


class CreateAssociationsInPythonForPortfolioTask(PuppetTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()

    @property
    def uid(self):
        return f"{self.__class__.__name__}/{self.account_id}--{self.region}--{self.portfolio}"

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.uid}.json"
        )

    def run(self):
        p = f'data/associations/{self.region}/{self.portfolio}/'
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        path = f'{p}/{self.account_id}.json'
        with open(path, 'w') as f:
            f.write("{}")

        portfolio_id = aws.get_portfolio_for(self.portfolio, self.account_id, self.region).get('Id')
        logging.info(f"{self.uid}: Creating the association for portfolio {portfolio_id}")
        with betterboto_client.ClientContextManager('servicecatalog', region_name=self.region) as servicecatalog:
            servicecatalog.associate_principal_with_portfolio(
                PortfolioId=portfolio_id,
                PrincipalARN=f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole",
                PrincipalType='IAM'
            )
        self.write_output(self.param_kwargs)


class CreateShareForAccountLaunchRegion(PuppetTask):
    """for the given account_id and launch and region create the shares"""
    account_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    deployment_map_for_account = luigi.DictParameter()
    launch_name = luigi.Parameter()
    launch_details = luigi.DictParameter()
    region = luigi.Parameter()

    @property
    def uid(self):
        return f"{self.__class__.__name__}/{self.account_id}--{self.launch_name}--{self.region}"

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.uid}.json"
        )

    def requires(self):
        logging.info(f"{self.uid}: expanded_from = {self.deployment_map_for_account.get('expanded_from')}")
        deps = {
            'topic': RequestPolicyTask(
                type="topic",
                region=self.region,
                organization=self.deployment_map_for_account.get('organization'),
                account_id=self.account_id,
            ),
            'bucket': RequestPolicyTask(
                type="bucket",
                region=self.region,
                organization=self.deployment_map_for_account.get('organization'),
                account_id=self.account_id,
            ),
        }
        portfolio = self.launch_details.get('portfolio')

        if self.account_id == self.puppet_account_id:
            # create an association
            deps['share'] = CreateAssociationsInPythonForPortfolioTask(
                self.account_id,
                self.region,
                portfolio,
            )
        else:
            deps['share'] = ShareAndAcceptPortfolioTask(
                self.account_id,
                self.region,
                portfolio,
                self.puppet_account_id,
            )
        return deps

    def run(self):
        self.write_output(self.param_kwargs)


class CreateShareForAccountLaunch(PuppetTask):
    """for the given account_id and launch create the shares"""
    account_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    deployment_map_for_account = luigi.DictParameter()
    launch_name = luigi.Parameter()
    launch_details = luigi.DictParameter()

    @property
    def uid(self):
        return f"{self.__class__.__name__}/{self.account_id}--{self.launch_name}"

    def requires(self):
        deps = {}
        mutable_deployment_map = dict(self.deployment_map_for_account)
        match = self.launch_details.get('match')
        logging.info(f"{self.uid}: Starting match was {match}")
        if match == "tag_match":
            matching_tag = self.launch_details.get('matching_tag')
            target_regions = None
            for tag_details in self.launch_details.get('deploy_to').get('tags'):
                if tag_details.get('tag') == matching_tag:
                    target_regions = tag_details.get('regions', 'default_region')
            assert target_regions is not None, "Could not find the tag for this provisioning"
            if target_regions == "default_region":
                target_regions = [mutable_deployment_map.get('default_region')]
            elif target_regions in ["enabled", "regions_enabled", "enabled_regions"]:
                target_regions = mutable_deployment_map.get('regions_enabled')
        elif match == "account_match":
            target_regions = None
            for accounts_details in self.launch_details.get('deploy_to').get('accounts'):
                if accounts_details.get('account_id') == self.account_id:
                    target_regions = accounts_details.get('regions', 'default_region')
            assert target_regions is not None, "Could not find the account_id for this provisioning"
            if target_regions == "default_region":
                target_regions = [mutable_deployment_map.get('default_region')]
            elif target_regions in ["enabled", "regions_enabled", "enabled_regions"]:
                target_regions = mutable_deployment_map.get('regions_enabled')

        else:
            raise Exception(f"{self.uid}: Unknown match: {match}")

        for region in target_regions:
            deps[f"{self.account_id}-{self.launch_name}-{region}"] = CreateShareForAccountLaunchRegion(
                self.account_id,
                self.puppet_account_id,
                self.deployment_map_for_account,
                self.launch_name,
                self.launch_details,
                region,
            )

        return deps

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.uid}.json"
        )

    def run(self):
        self.write_output(self.launch_details)


class CreateSharesForAccountImportMapTask(PuppetTask):
    """For the given account_id and deployment_map create the shares"""
    account_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    deployment_map_for_account = luigi.DictParameter()
    sharing_type = luigi.Parameter()

    @property
    def uid(self):
        return f"{self.account_id}-{self.sharing_type}"

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.__class__.__name__}/"
            f"{self.uid}.json"
        )

    @property
    def resources(self):
        return {}

    def params_for_results_display(self):
        return {
            "launch_name": 'na',
            "account_id": self.account_id,
            # "region": self.region,
            # "portfolio": self.portfolio,
            # "product": self.product,
            # "version": self.version,
        }

    def requires(self):
        launches = {}
        for launch_name, launch_details in self.deployment_map_for_account.get(self.sharing_type).items():
            launches[launch_name] = CreateShareForAccountLaunch(
                self.account_id, self.puppet_account_id, self.deployment_map_for_account, launch_name, launch_details
            )

        return {
            'launches': launches
        }

    def run(self):
        self.write_output(self.deployment_map_for_account)


def record_event(event_type, task, extra_event_data=None):
    task_type = task.__class__.__name__
    task_params = task.param_kwargs

    event = {
        "event_type": event_type,
        "task_type": task_type,
        "task_params": task_params,
        "params_for_results": task.params_for_results_display(),
    }
    if extra_event_data is not None:
        event.update(extra_event_data)

    with open(
            Path(constants.RESULTS_DIRECTORY) / event_type / f"{task_type}-{task.task_id}.json", 'w'
    ) as f:
        f.write(
            json.dumps(
                event,
                default=str,
                indent=4,
            )
        )


@luigi.Task.event_handler(luigi.Event.FAILURE)
def on_task_failure(task, exception):
    exception_details = {
        "exception_type": type(exception),
        "exception_stack_trace": traceback.format_exception(
            etype=type(exception),
            value=exception,
            tb=exception.__traceback__,
        )
    }
    record_event('failure', task, exception_details)


@luigi.Task.event_handler(luigi.Event.SUCCESS)
def on_task_success(task):
    record_event('success', task)


@luigi.Task.event_handler(luigi.Event.TIMEOUT)
def on_task_timeout(task):
    record_event('timeout', task)


@luigi.Task.event_handler(luigi.Event.PROCESS_FAILURE)
def on_task_process_failure(task, error_msg):
    exception_details = {
        "exception_type": 'PROCESS_FAILURE',
        "exception_stack_trace": error_msg,
    }
    record_event('process_failure', task, exception_details)


@luigi.Task.event_handler(luigi.Event.PROCESSING_TIME)
def on_task_processing_time(task, duration):
    record_event('processing_time', task, {"duration": duration})


@luigi.Task.event_handler(luigi.Event.BROKEN_TASK)
def on_task_broken_task(task, exception):
    record_event('broken_task', task, {"exception": exception})
