from betterboto import client as betterboto_client

from servicecatalog_puppet import aws

import luigi
import json

import logging

logger = logging.getLogger("tasks")


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
    parameter_name = luigi.Parameter()
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

    dependency = luigi.DictParameter()

    def requires(self):
        return ProvisionProductTask(**self.dependency)

    def output(self):
        return SSMParamTarget(self.param_name, False)

    def run(self):
        with betterboto_client.ClientContextManager('ssm') as ssm:
            outputs = json.loads(self.input().open('r').read()).get('Outputs')
            written = False
            for output in outputs:
                if output.get('OutputKey') == self.stack_output:
                    written = True
                    ssm.put_parameter(
                        Name=self.param_name,
                        Value=output.get('OutputValue'),
                        Type=self.param_type,
                        Overwrite=True,
                    )
            if not written:
                raise Exception("Could not write SSM Param from Provisioned Product. Wrong stack_output?")


class ProvisionProductTask(luigi.Task):
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

    status = luigi.Parameter(default='', significant=False)

    try_count = 1

    def add_requires(self, task):
        self.reqs.append(task)

    def requires(self):
        ssm_params = {}
        for param_input in self.ssm_param_inputs:
            ssm_params[param_input.get('parameter_name')] = GetSSMParamTask(**param_input)

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
        logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: "
                    f"starting deploy try {self.try_count} of {self.retry_count}")

        all_params = {}

        logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: collecting ssm params")
        for ssm_param_name, ssm_param in self.input().get('ssm_params', {}).items():
            all_params[ssm_param_name] = ssm_param.read()

        logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: collecting manifest params")
        for parameter in self.parameters:
            all_params[parameter.get('name')] = parameter.get('value')

        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.region}-{self.account_id}', region_name=self.region
        ) as service_catalog:
            logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: looking for previous failures")
            provisioned_product_id, provisioning_artifact_id = aws.terminate_if_status_is_not_available(
                service_catalog, self.launch_name, self.product_id, self.account_id, self.region
            )
            logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: "
                        f"provisioned_product_id: {provisioned_product_id}, "
                        f"provisioning_artifact_id : {provisioning_artifact_id}")

            with betterboto_client.CrossAccountClientContextManager(
                    'cloudformation', role, f'cfn-{self.region}-{self.account_id}', region_name=self.region
            ) as cloudformation:
                need_to_provision = True
                if provisioned_product_id:
                    default_cfn_params = aws.get_default_parameters_for_stack(cloudformation, f"SC-{self.account_id}-{provisioned_product_id}")
                else:
                    default_cfn_params = {}

                for default_cfn_param_name in default_cfn_params.keys():
                    if all_params.get(default_cfn_param_name) is None:
                        all_params[default_cfn_param_name] = default_cfn_params[default_cfn_param_name]
                if provisioning_artifact_id == self.version_id:
                    logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: found previous good provision")
                    if provisioned_product_id:
                        logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: checking params for diffs")
                        provisioned_parameters = aws.get_parameters_for_stack(
                            cloudformation,
                            f"SC-{self.account_id}-{provisioned_product_id}"
                        )
                        logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: "
                                    f"current params: {provisioned_parameters}")

                        logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: "
                                    f"new params: {all_params}")

                        if provisioned_parameters == all_params:
                            logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: params unchanged")
                            need_to_provision = False
                        else:
                            logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: params changed")

                if need_to_provision:
                    logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: about to provision with "
                                f"params: {json.dumps(all_params)}")

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
                                f"[{self.launch_name}] {self.account_id}:{self.region} :: current cfn stack_status is "
                                f"{stack_status}")
                            if stack_status not in ["UPDATE_COMPLETE", "CREATE_COMPLETE"]:
                                raise Exception(
                                    f"[{self.launch_name}] {self.account_id}:{self.region} :: current cfn stack_status is "
                                    f"{stack_status}"
                                )

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
                logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: finished provisioning")


class TerminateProductTask(luigi.Task):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()

    product_id = luigi.Parameter()
    version_id = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    retry_count = luigi.IntParameter(default=1)

    try_count = 1

    def output(self):
        return luigi.LocalTarget(
            f"output/TerminateProductTask/"
            f"{self.account_id}-{self.region}-{self.portfolio}-{self.product}-{self.version}.json"
        )

    def run(self):
        logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: "
                    f"starting terminate try {self.try_count} of {self.retry_count}")

        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        with betterboto_client.CrossAccountClientContextManager(
                'servicecatalog', role, f'sc-{self.region}-{self.account_id}', region_name=self.region
        ) as service_catalog:
            logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: looking for previous failures")
            provisioned_product_id, provisioning_artifact_id = aws.ensure_is_terminated(
                service_catalog, self.launch_name, self.product_id
            )
            log_output = self.to_str_params()
            log_output.update({
                "provisioned_product_id": provisioned_product_id,
            })
            f = self.output().open('w')
            f.write(
                json.dumps(
                    log_output,
                    indent=4,
                    default=str,
                )
            )
            f.close()
            logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: finished terminating")
