import time

from betterboto import client as betterboto_client

from servicecatalog_puppet import aws

import luigi
import json

import logging

logger = logging.getLogger(__file__)


class SSMParamTarget(luigi.Target):
    def __init__(self, param_name, error_when_not_found):
        super().__init__()
        self.param_name = param_name
        self.error_when_not_found = error_when_not_found

    def exists(self):
        with betterboto_client.ClientContextManager('ssm') as ssm:
            try:
                ssm.get_parameter(
                    Name=self.param_name,
                ).get('Parameter')
                return True
            except ssm.exceptions.ParameterNotFound as e:
                if self.error_when_not_found:
                    raise e
                return False

    def read(self):
        with betterboto_client.ClientContextManager('ssm') as ssm:
            return ssm.get_parameter(
                Name=self.param_name,
            ).get('Parameter').get('Value')


class GetSSMParamTask(luigi.Task):
    name = luigi.Parameter()
    region = luigi.Parameter(default=None)

    def output(self):
        return SSMParamTarget(self.name, True)

    def run(self):
        pass


class SetSSMParamFromProvisionProductTask(luigi.Task):
    param_name = luigi.Parameter()
    param_type = luigi.Parameter(default='String')
    stack_output = luigi.Parameter()

    dependency = luigi.Parameter()

    def requires(self):
        ProvisionProductTask(**self.dependency)

    def output(self):
        return SSMParamTarget(self.param_name, False)

    def run(self):
        with betterboto_client.ClientContextManager('ssm') as ssm:
            value = self.stack_output
            ssm.put_parameter(
                Name=self.param_name,
                Value=value,
                Type=self.param_type,
                Overwrite=True,
            )


class ProvisionProductTask(luigi.Task):
    delay = luigi.FloatParameter(significant=False)
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

    def add_requires(self, task):
        self.reqs.append(task)

    def requires(self):
        ssm_params = {}
        for param_input in self.ssm_param_inputs:
            ssm_params[param_input.get('name')] = GetSSMParamTask(**param_input)

        return {
            'dependencies': [
                self.__class__(**r) for r in self.dependencies
            ],
            'ssm_params': ssm_params
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/ProvisionProductTask/"
            f"{self.account_id}-{self.region}-{self.portfolio}-{self.product}-{self.version}.json"
        )

    def run(self):
        logger.info(
            f'starting main {self.launch_name} {self.portfolio} {self.product} {self.version} {self.account_id} {self.region}')
        time.sleep(self.delay)

        logger.info(f'doing cfn')

        all_params = {}

        for ssm_param_name, ssm_param in self.input().get('ssm_params', {}).items():
            all_params[ssm_param_name] = ssm_param.read()

        for parameter in self.parameters:
            all_params[parameter.get('name')] = parameter.get('value')

        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.region}-{self.account_id}', region_name=self.region
        ) as service_catalog:
            provisioned_product_id, provisioning_artifact_id = aws.terminate_if_status_is_not_available(
                service_catalog, self.launch_name, self.product_id
            )

            need_to_provision = True
            if provisioning_artifact_id == self.version_id:
                logger.info(
                    f"{self.launch_name} version {self.version_id} was already provisioned into {self.account_id}"
                )
                if provisioned_product_id:
                    logger.info(f"Checking to see if parameters have changed")
                    with betterboto_client.CrossAccountClientContextManager(
                            'cloudformation', role, f'cfn-{self.region}-{self.account_id}', region_name=self.region
                    ) as cloudformation:
                        provisioned_parameters = aws.get_parameters_for_stack(
                            cloudformation,
                            f"SC-{self.account_id}-{provisioned_product_id}"
                        )
                        if provisioned_parameters == all_params:
                            logger.info("Parameters the same, doing nothing")
                            need_to_provision = False
                        else:
                            logger.info("Parameters have changed, need to update")

            if need_to_provision:
                logger.info(f"Provisioning {self.launch_name} into account {self.account_id} {self.region}")
                provisioned_product_id = aws.provision_product(
                    service_catalog,
                    self.launch_name,
                    self.account_id,
                    self.region,
                    self.product_id,
                    self.version_id,
                    self.puppet_account_id,
                    aws.get_path_for_product(service_catalog, self.product_id),
                    all_params,
                    self.version,
                )

            f = self.output().open('w')
            with betterboto_client.CrossAccountClientContextManager(
                    'cloudformation', role, f'cfn-{self.region}-{self.account_id}', region_name=self.region
            ) as cloudformation:
                f.write(
                    json.dumps(
                        aws.get_stack_output_for(cloudformation, f"SC-{self.account_id}-{provisioned_product_id}"),
                        indent=4,
                        default=str,
                    )
                )
            f.close()
            logger.info(
                f'finished {self.launch_name} {self.portfolio} {self.product} {self.version} '
                f'for {self.account_id} {self.region}'
            )
