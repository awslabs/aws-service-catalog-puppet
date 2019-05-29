import sys
import time

from betterboto import client as betterboto_client

import luigi
import json

import logging

logger = logging.getLogger(__file__)


class GetSSMParamTask(luigi.Task):
    name = luigi.Parameter()
    region = luigi.Parameter(default=None)

    def output(self):
        return SSMParamTarget(self.name, True)

    def run(self):
        pass


class SetSSMParamTask(luigi.Task):
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


class ProvisionProductCloudFormationTask(luigi.Task):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()

    parameters = luigi.ListParameter()

    # @property
    # def resources(self):
    #     return { f"cloudformation-in-{self.account_id}-{self.region}": 1 }

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.portfolio}-{self.product}-{self.version}-{self.account_id}-{self.region}-cloudformation.log"
        )

    def run(self):
        f = self.output().open('w')
        f.write(
            json.dumps({
                'portfolio': self.portfolio,
                'product': self.product,
                'version': self.version,
                'account_id': self.account_id,
                'region': self.region,
            })
        )
        f.close()
        logger.info(f'finished {self.portfolio} {self.product} {self.version} {self.account_id} {self.region}')


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

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])
    dependencies = luigi.ListParameter(default=[])

    def add_requires(self, task):
        self.reqs.append(task)

    def requires(self):
        requirements = {
            'dependencies': [
                self.__class__(**r) for r in self.dependencies
            ],
            'ssm_params': [
               GetSSMParamTask(**param_input) for param_input in self.ssm_param_inputs
            ]
        }
        return requirements

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.portfolio}-{self.product}-{self.version}-{self.account_id}-{self.region}.log"
        )

    def run(self):
        logger.info(
            f'starting main {self.launch_name} {self.portfolio} {self.product} {self.version} {self.account_id} {self.region}')
        time.sleep(self.delay)

        logger.info(f'doing cfn')
        parameters = []
        yield ProvisionProductCloudFormationTask(
            self.launch_name,
            self.portfolio,
            self.product,
            self.version,
            self.account_id,
            self.region,
            parameters,
        )

        logger.info(f'writing to file')
        f = self.output().open('w')
        f.write(
            json.dumps({
                'portfolio': self.portfolio,
                'product': self.product,
                'version': self.version,
                'account_id': self.account_id,
                'region': self.region,
            })
        )
        f.close()


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
            ssm.get_parameter(
                Name=self.param_name,
            ).get('Parameter')


@luigi.Task.event_handler(luigi.Event.FAILURE)
def mourn_failure(task, exception):
    logger.error('THERE WAS A FAILURE')
    sys.exit(luigi.retcodes.retcode().unhandled_exception)\


@luigi.Task.event_handler(luigi.Event.BROKEN_TASK)
def mourn_failure(task, exception):
    logger.error('THERE WAS A BROKEN_TASK')
    sys.exit(luigi.retcodes.retcode().unhandled_exception)


@luigi.Task.event_handler(luigi.Event.DEPENDENCY_MISSING)
def mourn_failure(task, exception):
    logger.error('THERE WAS A DEPENDENCY_MISSING')
    sys.exit(luigi.retcodes.retcode().unhandled_exception)
