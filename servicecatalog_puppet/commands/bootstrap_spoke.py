from jinja2 import Template

import logging


from servicecatalog_puppet.asset_helpers import read_from_site_packages
from servicecatalog_puppet.constants import BOOTSTRAP_STACK_NAME


logger = logging.getLogger(__file__)


def do_bootstrap_spoke(puppet_account_id, cloudformation, puppet_version):
    logger.info('Starting bootstrap of spoke')
    template = read_from_site_packages('{}-spoke.template.yaml'.format(BOOTSTRAP_STACK_NAME))
    template = Template(template).render(VERSION=puppet_version)
    args = {
        'StackName': "{}-spoke".format(BOOTSTRAP_STACK_NAME),
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
    logger.info('Finished bootstrap of spoke')
