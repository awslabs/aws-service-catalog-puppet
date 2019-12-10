import json
import time

import luigi
from betterboto import client as betterboto_client

from servicecatalog_puppet import aws
from servicecatalog_puppet import config

from servicecatalog_puppet import constants
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

    @property
    def uid(self):
        return f"{self.__class__.__name__}/" \
               f"{self.portfolio}--{self.product}--{self.version}--{self.account_id}--{self.region}"

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.uid}.json"
        )

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

    dependencies = luigi.ListParameter(default=[], significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    should_use_sns = luigi.BoolParameter(significant=False, default=False)
    should_use_product_plans = luigi.BoolParameter(significant=False, default=False)
    requested_priority = luigi.IntParameter(significant=False, default=0)

    pre_actions = luigi.ListParameter(default=[], significant=False)
    post_actions = luigi.ListParameter(default=[], significant=False)

    try_count = 1
    all_params = []

    @property
    def uid(self):
        return f"{self.launch_name}-{self.account_id}-{self.region}-{self.portfolio}-{self.product}-{self.version}"

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

        dependencies = []
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
            'provisioning_artifact_parameters': ProvisioningArtifactParametersTask(
                self.portfolio,
                self.product,
                self.version,
                self.account_id,
                self.region,
            ),
            'pre_actions': [portfoliomanagement.ProvisionActionTask(**p) for p in self.pre_actions],
        }

    @property
    def node_id(self):
        return "_".join([
            self.launch_name,
            self.portfolio,
            self.product,
            self.version,
            self.account_id,
            self.region,
        ])

    def graph_node(self):
        label = f"<b>ProvisionProduct</b><br/>Launch: {self.launch_name}<br/>Portfolio: {self.portfolio}<br/>Product: {self.product}<br/>Version: {self.version}<br/>AccountId: {self.account_id}<br/>Region: {self.region}"
        return f"\"{self.__class__.__name__}_{self.node_id}\" [fillcolor=lawngreen style=filled label= < {label} >]"

    def get_graph_lines(self):
        return [
            f"\"{ProvisionProductTask.__name__}_{self.node_id}\" -> \"{ProvisionProductTask.__name__}_{'_'.join([dep.get('launch_name'), dep.get('portfolio'), dep.get('product'), dep.get('version'), dep.get('account_id'), dep.get('region')])}\""
            for dep in self.dependencies
        ]

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
            f"output/{self.__class__.__name__}/"
            f"{self.uid}.json"
        )

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

                for p in self.post_actions:
                    yield portfoliomanagement.ProvisionActionTask(**p)

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
    dependencies = luigi.ListParameter(default=[])

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

    try_count = 1

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])
    dependencies = luigi.ListParameter(default=[])

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


class ResetProvisionedProductOwnerTask(tasks.PuppetTask):
    launch_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return self.param_kwargs

    def output(self):
        return luigi.LocalTarget(
            f"output/ResetProvisionedProductOwnerTask/"
            f"{self.launch_name}-{self.account_id}-{self.region}.json"
        )

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
