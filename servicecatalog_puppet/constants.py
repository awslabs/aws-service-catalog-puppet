import os

PREFIX = 'SC-P--'
BOOTSTRAP_STACK_NAME = "servicecatalog-puppet"
PIPELINE_NAME = "servicecatalog-puppet-pipeline"
SERVICE_CATALOG_PUPPET_REPO_NAME = "ServiceCatalogPuppet"
OUTPUT = "output"
TEMPLATES = os.path.sep.join([OUTPUT, "templates"])
LAUNCHES_PATH = os.path.sep.join([OUTPUT, "launches"])
CONFIG_PARAM_NAME = "/servicecatalog-puppet/config"
CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN = "/servicecatalog-puppet/org-iam-role-arn"
PUPPET_ORG_ROLE_FOR_EXPANDS_ARN = "PuppetOrgRoleForExpandsArn"
HOME_REGION_PARAM_NAME = "/servicecatalog-puppet/home-region"

PROVISIONED = 'provisioned'
TERMINATED = 'terminated'

DEFAULT_TIMEOUT = 0
LAUNCHES = 'launches'
SPOKE_LOCAL_PORTFOLIOS = 'spoke-local-portfolios'

DISALLOWED_ATTRIBUTES_FOR_TERMINATED_LAUNCHES = [
    'depends_on',
    'outputs',
    'parameters',
]

RESULTS_DIRECTORY = "results"