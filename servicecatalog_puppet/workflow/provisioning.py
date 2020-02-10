import json
from copy import deepcopy

import luigi
from betterboto import client as betterboto_client

from servicecatalog_puppet import manifest_utils_for_launches
from servicecatalog_puppet import manifest_utils_for_spoke_local_portfolios
from servicecatalog_puppet import aws
from servicecatalog_puppet import config

from servicecatalog_puppet import constants, manifest_utils
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow import portfoliomanagement

import logging

logger = logging.getLogger("tasks")


class ProvisioningArtifactParametersTask(tasks.PuppetTask):
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    retry_count = 5

    def params_for_results_display(self):
        return {
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
            "account_id": self.account_id,
            "region": self.region,
        }

    def requires(self):
        return {
            'details': portfoliomanagement.GetVersionIdByVersionName(
                self.portfolio,
                self.product,
                self.version,
                self.account_id,
                self.region,
            ),
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_parameters_{self.account_id}_{self.region}",
        ]

    def run(self):
        with self.input().get('details').open('r') as f:
            details = json.loads(f.read())
            with betterboto_client.CrossAccountClientContextManager(
                    'servicecatalog',
                    f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole",
                    f"{self.account_id}-{self.region}-sc",
                    region_name=self.region,
            ) as service_catalog:
                logger.info(f"{self.uid}: getting path for {details.get('product_id')} of portfolio: {self.portfolio}")
                path_id = aws.get_path_for_product(service_catalog, details.get('product_id'), self.portfolio)
                provisioning_artifact_parameters = service_catalog.describe_provisioning_parameters(
                    ProductId=details.get('product_id'),
                    ProvisioningArtifactId=details.get('version_id'),
                    PathId=path_id,
                ).get('ProvisioningArtifactParameters', [])
                self.write_output(provisioning_artifact_parameters)


class ProvisionProductTask(tasks.PuppetTask):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    parameters = luigi.ListParameter(default=[], significant=False)
    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    should_use_sns = luigi.BoolParameter(significant=False, default=False)
    should_use_product_plans = luigi.BoolParameter(significant=False, default=False)
    requested_priority = luigi.IntParameter(significant=False, default=0)

    try_count = 1
    all_params = []

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
        }

    @property
    def priority(self):
        return self.requested_priority

    def requires(self):
        all_params = {}
        all_params.update(self.manifest_parameters)
        all_params.update(self.launch_parameters)
        all_params.update(self.account_parameters)

        ssm_params = {}

        for param_name, param_details in all_params.items():
            if param_details.get('ssm'):
                if param_details.get('default'):
                    del param_details['default']
                ssm_params[param_name] = tasks.GetSSMParamTask(
                    parameter_name=param_name,
                    name=param_details.get('ssm').get('name'),
                    region=param_details.get('ssm').get('region', config.get_home_region())
                )
        self.all_params = all_params

        version_id = portfoliomanagement.GetVersionIdByVersionName(
            self.portfolio,
            self.product,
            self.version,
            self.account_id,
            self.region,
        )
        product_id = portfoliomanagement.GetProductIdByProductName(
            self.portfolio,
            self.product,
            self.account_id,
            self.region,
        )

        return {
            'ssm_params': ssm_params,
            'version': version_id,
            'product': product_id,
            'provisioning_artifact_parameters': ProvisioningArtifactParametersTask(
                self.portfolio,
                self.product,
                self.version,
                self.account_id,
                self.region,
            ),
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.search_provisioned_products_{self.account_id}_{self.region}",

            f"servicecatalog.describe_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.terminate_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_record_{self.account_id}_{self.region}",

            f"cloudformation.get_template_summary_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",

            f"servicecatalog.list_provisioned_product_plans_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.delete_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.create_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.execute_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.provision_product_{self.account_id}_{self.region}",

            # f"ssm.put_parameter_and_wait_{self.region}",
        }

    def run(self):
        logger.info(f"[{self.uid}] starting deploy try {self.try_count} of {self.retry_count}")

        product_id, version_id = self.get_product_and_version_ids()

        all_params = self.get_all_params()

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

                logging.info(
                    f"running as {role},checking {product_id} {version_id} {path_id} in {self.account_id} {self.region}"
                )

                with self.input().get('provisioning_artifact_parameters').open('r') as f:
                    provisioning_artifact_parameters = json.loads(f.read())

                params_to_use = {}
                for p in provisioning_artifact_parameters:
                    param_name = p.get('ParameterKey')
                    params_to_use[param_name] = all_params.get(param_name, p.get('DefaultValue'))

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

                        logger.info(f"[{self.uid}] new params: {params_to_use}")

                        if provisioned_parameters == params_to_use:
                            logger.info(f"[{self.uid}] params unchanged")
                            need_to_provision = False
                        else:
                            logger.info(f"[{self.uid}] params changed")

                if need_to_provision:
                    logger.info(f"[{self.uid}] about to provision with params: {json.dumps(params_to_use)}")

                    if provisioned_product_id:
                        stack = aws.get_stack_output_for(
                            cloudformation,
                            f"SC-{self.account_id}-{provisioned_product_id}"
                        )
                        stack_status = stack.get('StackStatus')
                        logger.info(
                            f"[{self.uid}] current cfn stack_status is {stack_status}")
                        if stack_status not in ["UPDATE_COMPLETE", "CREATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"]:
                            raise Exception(
                                f"[{self.uid}] current cfn stack_status is {stack_status}"
                            )
                        if stack_status == "UPDATE_ROLLBACK_COMPLETE":
                            logger.warning(
                                f"[{self.uid}] SC-{self.account_id}-{provisioned_product_id} has a status of "
                                f"{stack_status}.  This may need manual resolution."
                            )

                    if provisioned_product_id:
                        if self.should_use_product_plans:
                            provisioned_product_id = aws.provision_product_with_plan(
                                service_catalog,
                                self.launch_name,
                                self.account_id,
                                self.region,
                                product_id,
                                version_id,
                                self.puppet_account_id,
                                path_id,
                                params_to_use,
                                self.version,
                                self.should_use_sns,
                            )
                        else:
                            provisioned_product_id = aws.update_provisioned_product(
                                service_catalog,
                                self.launch_name,
                                self.account_id,
                                self.region,
                                product_id,
                                version_id,
                                self.puppet_account_id,
                                path_id,
                                params_to_use,
                                self.version,
                            )

                    else:
                        provisioned_product_id = aws.provision_product(
                            service_catalog,
                            self.launch_name,
                            self.account_id,
                            self.region,
                            product_id,
                            version_id,
                            self.puppet_account_id,
                            path_id,
                            params_to_use,
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
                        # TODO push into another task
                        for output in stack_details.get('Outputs', []):
                            if output.get('OutputKey') == ssm_param_output.get('stack_output'):
                                found_match = True
                                logger.info(f"[{self.uid}] found value")
                                ssm.put_parameter_and_wait(
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

    def get_all_params(self):
        all_params = {}
        logger.info(f"[{self.uid}] :: collecting all_params")
        for param_name, param_details in self.all_params.items():
            if param_details.get('ssm'):
                with self.input().get('ssm_params').get(param_name).open() as f:
                    all_params[param_name] = json.loads(f.read()).get('Value')
            if param_details.get('default'):
                all_params[param_name] = param_details.get('default')
        logger.info(f"[{self.uid}] :: finished collecting all_params: {all_params}")
        return all_params

    def get_product_and_version_ids(self):
        with self.input().get('version').open('r') as f:
            version_id = json.loads(f.read()).get('version_id')
        with self.input().get('product').open('r') as f:
            product_id = json.loads(f.read()).get('product_id')
        return product_id, version_id


class ProvisionProductDryRunTask(ProvisionProductTask):
    def api_calls_used(self):
        return [
            f"servicecatalog.search_provisioned_products_{self.account_id}_{self.region}",
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_artifact_{self.account_id}_{self.region}",

            f"cloudformation.describe_provisioning_artifact_{self.account_id}_{self.region}",
            f"cloudformation.get_template_summary_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
        ]

    def run(self):
        logger.info(f"[{self.uid}] starting deploy try {self.try_count} of {self.retry_count}")

        product_id, version_id = self.get_product_and_version_ids()

        all_params = self.get_all_params()

        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.region}-{self.account_id}', region_name=self.region
        ) as service_catalog:
            logger.info(f"[{self.uid}] looking for previous failures")
            path_id = aws.get_path_for_product(service_catalog, product_id, self.portfolio)

            response = service_catalog.search_provisioned_products(
                Filters={'SearchQuery': [
                    "productId:{}".format(product_id)
                ]}
            )
            provisioned_product_id = False
            provisioning_artifact_id = False
            for r in response.get('ProvisionedProducts', []):
                if r.get('Name') == self.launch_name:
                    current_status = r.get('Status')
                    if current_status in ["AVAILABLE", "TAINTED"]:
                        provisioned_product_id = r.get('Id')
                        provisioning_artifact_id = r.get('ProvisioningArtifactId')

            logger.info(f"[{self.uid}] pp_id: {provisioned_product_id}, paid : {provisioning_artifact_id}")

            with betterboto_client.CrossAccountClientContextManager(
                    'cloudformation', role, f'cfn-{self.region}-{self.account_id}', region_name=self.region
            ) as cloudformation:
                logging.info(
                    f"running as {role},checking {product_id} {version_id} {path_id} in {self.account_id} {self.region}"
                )

                with self.input().get('provisioning_artifact_parameters').open('r') as f:
                    provisioning_artifact_parameters = json.loads(f.read())

                params_to_use = {}
                for p in provisioning_artifact_parameters:
                    param_name = p.get('ParameterKey')
                    params_to_use[param_name] = all_params.get(param_name, p.get('DefaultValue'))

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
                        logger.info(f"[{self.uid}] new params: {params_to_use}")

                        if provisioned_parameters == params_to_use:
                            logger.info(f"[{self.uid}] params unchanged")
                            self.write_result(
                                current_version=self.version,
                                new_version=self.version,
                                effect=constants.NO_CHANGE,
                                notes="Versions and params are the same",
                            )
                        else:
                            self.write_result(
                                current_version=self.version,
                                new_version=self.version,
                                effect=constants.CHANGE,
                                notes="Versions are the same but the params are different",
                            )
                else:
                    if provisioning_artifact_id:
                        current_version = self.get_current_version(provisioning_artifact_id, service_catalog)
                    else:
                        current_version = ""
                    self.write_result(
                        current_version=current_version,
                        new_version=self.version,
                        effect=constants.CHANGE,
                        notes='Version change',
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


class TerminateProductTask(tasks.PuppetTask):
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
    # dependencies = luigi.ListParameter(default=[])

    def requires(self):
        product_id = portfoliomanagement.GetProductIdByProductName(
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

    def api_calls_used(self):
        return [
            f"servicecatalog.search_provisioned_products_{self.account_id}_{self.region}",
            f"servicecatalog.terminate_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_record_{self.account_id}_{self.region}",
            # f"ssm.delete_parameter_{self.region}": 1,
        ]

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
                        # todo push into another task
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


class TerminateProductDryRunTask(tasks.PuppetTask):
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

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])
    # dependencies = luigi.ListParameter(default=[])

    try_count = 1

    def requires(self):
        product_id = portfoliomanagement.GetProductIdByProductName(
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

    def api_calls_used(self):
        return [
            f"servicecatalog.search_provisioned_products_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_artifact_{self.account_id}_{self.region}",
        ]

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


class ResetProvisionedProductOwnerTask(tasks.PuppetTask):
    launch_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.search_provisioned_products_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioned_product_properties_{self.account_id}_{self.region}",
        ]

    def run(self):
        logger_prefix = f"[{self.launch_name}] {self.account_id}:{self.region}"
        logger.info(
            f"{logger_prefix} :: starting ResetProvisionedProductOwnerTask"
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


class LaunchTask(tasks.PuppetTask):
    launch_name = luigi.Parameter()
    manifest = luigi.DictParameter()
    puppet_account_id = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
        }

    def requires(self):
        launch = self.manifest.get('launches').get(self.launch_name)

        return {
            'other_launches': [
                self.__class__(
                    launch_name=dependency,
                    manifest=self.manifest,
                    puppet_account_id=self.puppet_account_id,
                    should_use_sns=self.should_use_sns,
                    should_use_product_plans=self.should_use_product_plans,
                    include_expanded_from=self.include_expanded_from,
                    single_account=self.single_account,
                    is_dry_run=self.is_dry_run,
                ) for dependency in launch.get('depends_on', [])
            ]
        }

    def generate_provisions(self, task_defs):
        provisions = []

        # task_defs = launch_task_def.get('task_defs')
        for task_def in task_defs:
            if self.single_account is not None:
                if task_def.get('account_id') != self.single_account:
                    continue

            task_status = task_def.get('status')
            del task_def['status']
            del task_def['depends_on']
            task_def['is_dry_run'] = self.is_dry_run

            if task_status == constants.PROVISIONED:
                provisioning_parameters = {}
                for p in ProvisionProductTask.get_param_names(include_significant=True):
                    provisioning_parameters[p] = task_def.get(p)

                if self.is_dry_run:
                    provisions.append(
                        ProvisionProductDryRunTask(**provisioning_parameters)
                    )
                else:
                    provisions.append(
                        ProvisionProductTask(**provisioning_parameters)
                    )

            elif task_status == constants.TERMINATED:
                terminating_parameters = {}
                for p in TerminateProductTask.get_param_names(include_significant=True):
                    terminating_parameters[p] = task_def.get(p)

                if self.is_dry_run:
                    provisions.append(
                        TerminateProductDryRunTask(**terminating_parameters)
                    )
                else:
                    provisions.append(
                        TerminateProductTask(**terminating_parameters)
                    )
            else:
                raise Exception(f"Unsupported status of {task_status}")
        return provisions

    def run(self):
        launch_tasks_def = manifest_utils_for_launches.generate_launch_task_defs_for_launch(
            self.launch_name,
            self.manifest,
            self.puppet_account_id,
            self.should_use_sns,
            self.should_use_product_plans,
            self.include_expanded_from,
            self.single_account,
            self.is_dry_run
        )

        logger.info(f"{self.uid} starting pre actions")
        yield [portfoliomanagement.ProvisionActionTask(**p) for p in launch_tasks_def.get('pre_actions', [])]
        logger.info(f"{self.uid} finished pre actions")

        logger.info(f"{self.uid} starting launches")
        ls = self.generate_provisions(launch_tasks_def.get('task_defs', []))
        yield ls
        logger.info(f"{self.uid} finished launches")

        logger.info(f"{self.uid} starting post actions")
        yield [portfoliomanagement.ProvisionActionTask(**p) for p in launch_tasks_def.get('post_actions', [])]
        logger.info(f"{self.uid} finished post actions")

        self.write_output(self.params_for_results_display())


class SpokeLocalPortfolioTask(tasks.PuppetTask):
    spoke_local_portfolio_name = luigi.Parameter()
    manifest = luigi.DictParameter()
    puppet_account_id = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()

    def params_for_results_display(self):
        return {
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
        }

    def requires(self):
        spoke_local_portfolio = self.manifest.get('spoke-local-portfolios').get(self.spoke_local_portfolio_name)

        return {
            'other_launches': [
                LaunchTask(
                    launch_name=dependency,
                    manifest=self.manifest,
                    puppet_account_id=self.puppet_account_id,
                    should_use_sns=self.should_use_sns,
                    should_use_product_plans=self.should_use_product_plans,
                    include_expanded_from=self.include_expanded_from,
                    single_account=self.single_account,
                    is_dry_run=self.is_dry_run,
                ) for dependency in spoke_local_portfolio.get('depends_on', [])
            ]
        }

    def generate_tasks(self, task_defs):
        first_task_def = task_defs[0]
        logger.info('first_task_def')
        portfolio = first_task_def.get('portfolio')
        tasks = []

        for task_def in task_defs:
            create_spoke_local_portfolio_task_params = {
                'account_id': task_def.get('account_id'),
                'region': task_def.get('region'),
                'portfolio': portfolio,
                # 'pre_actions': task_def.get('pre_actions'),
                'organization': task_def.get('organization')
            }
            create_spoke_local_portfolio_task = portfoliomanagement.CreateSpokeLocalPortfolioTask(
                **create_spoke_local_portfolio_task_params,
            )
            tasks.append(create_spoke_local_portfolio_task)

            create_spoke_local_portfolio_task_as_dependency_params = {
                'account_id': task_def.get('account_id'),
                'region': task_def.get('region'),
                'portfolio': portfolio,
                'organization': task_def.get('organization'),
            }

            if len(task_def.get('associations', [])) > 0:
                create_associations_for_portfolio_task = portfoliomanagement.CreateAssociationsForPortfolioTask(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    associations=task_def.get('associations'),
                    puppet_account_id=task_def.get('puppet_account_id'),
                    should_use_sns=task_def.get('should_use_sns'),
                    # dependencies=dependencies,
                    # pre_actions=task_def.get('pre_actions'),
                )
                tasks.append(create_associations_for_portfolio_task)

            launch_constraints = task_def.get('constraints', {}).get('launch', [])

            import_into_spoke_local_portfolio_task = portfoliomanagement.ImportIntoSpokeLocalPortfolioTask(
                **create_spoke_local_portfolio_task_as_dependency_params,
                puppet_account_id=task_def.get('puppet_account_id'),
            )
            tasks.append(import_into_spoke_local_portfolio_task)

            if len(launch_constraints) > 0:
                create_launch_role_constraints_for_portfolio_task_params = {
                    'launch_constraints': launch_constraints,
                    'puppet_account_id': task_def.get('puppet_account_id'),
                    'should_use_sns': task_def.get('should_use_sns'),
                }
                create_launch_role_constraints_for_portfolio = portfoliomanagement.CreateLaunchRoleConstraintsForPortfolio(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    **create_launch_role_constraints_for_portfolio_task_params,
                    # dependencies=dependencies,
                )
                tasks.append(create_launch_role_constraints_for_portfolio)
        return tasks

    def run(self):
        tasks_defs = manifest_utils_for_spoke_local_portfolios.generate_spoke_local_portfolios_tasks_for_spoke_local_portfolio(
            self.spoke_local_portfolio_name,
            self.manifest,
            self.puppet_account_id,
            self.should_use_sns,
            self.should_use_product_plans,
            self.include_expanded_from,
            self.single_account,
            self.is_dry_run,
        )

        logger.info(f"spoke_local_portfolio_name is {self.spoke_local_portfolio_name}")

        logger.info(f"{self.uid} starting pre actions")
        yield [portfoliomanagement.ProvisionActionTask(**p) for p in tasks_defs.get('pre_actions', [])]
        logger.info(f"{self.uid} finished pre actions")

        logger.info(f"{self.uid} starting launches")
        yield self.generate_tasks(tasks_defs.get('task_defs', []))
        logger.info(f"{self.uid} finished launches")

        logger.info(f"{self.uid} starting post actions")
        yield [portfoliomanagement.ProvisionActionTask(**p) for p in tasks_defs.get('post_actions', [])]
        logger.info(f"{self.uid} finished post actions")

        self.write_output(self.params_for_results_display())
