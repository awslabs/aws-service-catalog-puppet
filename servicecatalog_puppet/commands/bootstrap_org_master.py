from jinja2 import Template

import logging


from servicecatalog_puppet.asset_helpers import read_from_site_packages
from servicecatalog_puppet.constants import BOOTSTRAP_STACK_NAME
from servicecatalog_puppet.constants import PUPPET_ORG_ROLE_FOR_EXPANDS_ARN

logger = logging.getLogger(__file__)


def do_bootstrap_org_master(puppet_account_id, cloudformation, puppet_version):
    logger.info('Starting bootstrap of org master')
    stack_name = "{}-org-master".format(BOOTSTRAP_STACK_NAME)
    template = read_from_site_packages('{}.template.yaml'.format(stack_name))
    template = Template(template).render(VERSION=puppet_version)
    args = {
        'StackName': stack_name,
        'TemplateBody': template,
        'Capabilities': ['CAPABILITY_NAMED_IAM'],
        'Parameters': [
            {
                'ParameterKey': 'PuppetAccountId',
                'ParameterValue': str(puppet_account_id),
            }, {
                'ParameterKey': 'Version',
                'ParameterValue': puppet_version,
                'UsePreviousValue': False,
            },
        ],
    }
    cloudformation.create_or_update(**args)
    response = cloudformation.describe_stacks(StackName=stack_name)
    if len(response.get('Stacks')) != 1:
        raise Exception("Expected there to be only one {} stack".format(stack_name))
    stack = response.get('Stacks')[0]

    for output in stack.get('Outputs'):
        if output.get('OutputKey') == PUPPET_ORG_ROLE_FOR_EXPANDS_ARN:
            logger.info('Finished bootstrap of org-master')
            return output.get("OutputValue")

    raise Exception("Could not find output: {} in stack: {}".format(PUPPET_ORG_ROLE_FOR_EXPANDS_ARN, stack_name))

