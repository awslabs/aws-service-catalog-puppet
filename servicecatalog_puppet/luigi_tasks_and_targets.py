import time

from betterboto import client as betterboto_client

from servicecatalog_puppet import aws, cli_command_helpers

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

    worker_timeout = luigi.IntParameter(default=0, significant=False)

    ssm_param_outputs = luigi.ListParameter(default=[])

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
                    default_cfn_params = aws.get_default_parameters_for_stack(
                        cloudformation, f"SC-{self.account_id}-{provisioned_product_id}"
                    )
                else:
                    default_cfn_params = {}

                for default_cfn_param_name in default_cfn_params.keys():
                    if all_params.get(default_cfn_param_name) is None:
                        all_params[default_cfn_param_name] = default_cfn_params[default_cfn_param_name]
                if provisioning_artifact_id == self.version_id:
                    logger.info(
                        f"[{self.launch_name}] {self.account_id}:{self.region} :: found previous good provision")
                    if provisioned_product_id:
                        logger.info(
                            f"[{self.launch_name}] {self.account_id}:{self.region} :: checking params for diffs")
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

                with betterboto_client.CrossAccountClientContextManager(
                        'cloudformation', role, f'cfn-{self.region}-{self.account_id}', region_name=self.region
                ) as spoke_cloudformation:
                    stack_details = aws.get_stack_output_for(
                        spoke_cloudformation, f"SC-{self.account_id}-{provisioned_product_id}"
                    )

                for ssm_param_output in self.ssm_param_outputs:
                    logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: "
                                f"writing SSM Param: {ssm_param_output.get('stack_output')}")
                    with betterboto_client.ClientContextManager('ssm') as ssm:
                        found_match = False
                        for output in stack_details.get('Outputs', []):
                            if output.get('OutputKey') == ssm_param_output.get('stack_output'):
                                found_match = True
                                logger.info(f"[{self.launch_name}] {self.account_id}:{self.region} :: found value")
                                ssm.put_parameter(
                                    Name=ssm_param_output.get('param_name'),
                                    Value=output.get('OutputValue'),
                                    Type=ssm_param_output.get('param_type', 'String'),
                                    Overwrite=True,
                                )
                        if not found_match:
                            raise Exception(f"[{self.launch_name}] {self.account_id}:{self.region} :: Could not find "
                                            f"match for {ssm_param_output.get('stack_output')}")

                f = self.output().open('w')
                f.write(
                    json.dumps(
                        stack_details,
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

    worker_timeout = luigi.IntParameter(default=0, significant=False)

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


class CreateSpokeLocalPortfolioTask(luigi.Task):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()

    provider_name = luigi.Parameter(significant=False, default='not set')
    description = luigi.Parameter(significant=False, default='not set')

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
        f = self.output().open('w')
        f.write(
            json.dumps(
                spoke_portfolio,
                indent=4,
                default=str,
            )
        )
        f.close()
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: finished creating portfolio")


class CreateAssociationsForPortfolioTask(luigi.Task):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    associations = luigi.ListParameter(default=[])
    dependencies = luigi.ListParameter(default=[])

    def requires(self):
        return {
            'create_spoke_local_portfolio_task': CreateSpokeLocalPortfolioTask(
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
            ),
            'deps': [ProvisionProductTask(**dependency) for dependency in self.dependencies]
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/CreateAssociationsForPortfolioTask/"
            f"{self.account_id}-{self.region}-{self.portfolio}.json"
        )

    def run(self):
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: starting creating associations")
        role = f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"

        portfolio_id = json.loads(self.input().get('create_spoke_local_portfolio_task').open('r').read()).get('Id')
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
                ],
            )
            result = cloudformation.describe_stacks(
                StackName=stack_name,
            ).get('Stacks')[0]
            f = self.output().open('w')
            f.write(
                json.dumps(
                    result,
                    indent=4,
                    default=str,
                )
            )
            f.close()
            logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: Finished importing")


class ImportIntoSpokeLocalPortfolioTask(luigi.Task):
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
                product_view_summary = product_view_detail.get('ProductViewSummary')
                hub_product_name = product_view_summary.get('Name')
                hub_product_id = product_view_summary.get('ProductId')

                product_versions_that_should_be_copied = {}
                hub_provisioning_artifact_details = service_catalog.list_provisioning_artifacts(
                    ProductId=hub_product_id
                ).get('ProvisioningArtifactDetails', [])
                for hub_provisioning_artifact_detail in hub_provisioning_artifact_details:
                    if hub_provisioning_artifact_detail.get('Active') and hub_provisioning_artifact_detail.get(
                            'Type') == 'CLOUD_FORMATION_TEMPLATE':
                        product_versions_that_should_be_copied[
                            f"{hub_provisioning_artifact_detail.get('Name')}"] = hub_provisioning_artifact_detail

                logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: Copying {hub_product_name}")
                hub_product_arn = product_view_detail.get('ProductARN')
                copy_args = {'SourceProductArn': hub_product_arn}
                spoke_portfolio = json.loads(self.input().open('r').read())
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
                                copy_args['TargetProductId'] = spoke_product_view.get('ProductId')
                                spoke_provisioning_artifact_details = spoke_service_catalog.list_provisioning_artifacts(
                                    ProductId=spoke_product_view.get('ProductId')
                                ).get('ProvisioningArtifactDetails')
                                for provisioning_artifact_detail in spoke_provisioning_artifact_details:
                                    id_to_delete = f"{provisioning_artifact_detail.get('Name')}"
                                    if product_versions_that_should_be_copied.get(id_to_delete, None) is not None:
                                        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} "
                                                    f"{hub_product_name} :: Going to skip "
                                                    f"{spoke_product_view.get('ProductId')} "
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

        f = self.output().open('w')
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
        f.close()
        logger.info(f"[{self.portfolio}] {self.account_id}:{self.region} :: Finished importing")


class CreateLaunchRoleConstraintsForPortfolio(luigi.Task):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    hub_portfolio_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    launch_constraints = luigi.DictParameter()

    dependencies = luigi.ListParameter(default=[])

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
        dependency_output = json.loads(self.input().get('create_spoke_local_portfolio_task').open('r').read())
        spoke_portfolio = dependency_output.get('portfolio')
        portfolio_id = spoke_portfolio.get('Id')
        product_name_to_id_dict = dependency_output.get('products')
        with betterboto_client.CrossAccountClientContextManager(
                'cloudformation', role, f'cfn-{self.account_id}-{self.region}', region_name=self.region
        ) as cloudformation:
            template = cli_command_helpers.env.get_template('launch_role_constraints.template.yaml.j2').render(
                portfolio={
                    'DisplayName': self.portfolio,
                },
                portfolio_id=portfolio_id,
                launch_constraints=self.launch_constraints,
                product_name_to_id_dict=product_name_to_id_dict,
            )
            time.sleep(60)
            stack_name = f"launch-constraints-for-portfolio-{portfolio_id}"
            cloudformation.create_or_update(
                StackName=stack_name,
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:aws:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ],
            )
            result = cloudformation.describe_stacks(
                StackName=stack_name,
            ).get('Stacks')[0]
            f = self.output().open('w')
            f.write(
                json.dumps(
                    result,
                    indent=4,
                    default=str,
                )
            )
            f.close()

    def output(self):
        return luigi.LocalTarget(
            f"output/CreateLaunchRoleConstraintsForPortfolio/"
            f"{self.account_id}-{self.region}-{self.portfolio}-{self.hub_portfolio_id}.json"
        )
