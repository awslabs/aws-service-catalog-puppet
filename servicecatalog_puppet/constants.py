import os

PREFIX = 'SC-P--'
BOOTSTRAP_STACK_NAME = "servicecatalog-puppet"
SERVICE_CATALOG_PUPPET_REPO_NAME = "ServiceCatalogPuppet"
OUTPUT = "output"
TEMPLATES = os.path.sep.join([OUTPUT, "templates"])
LAUNCHES = os.path.sep.join([OUTPUT, "launches"])
HOME_REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')
CONFIG_PARAM_NAME = "/servicecatalog-puppet/config"
CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN = "/servicecatalog-puppet/org-iam-role-arn"
PUPPET_ORG_ROLE_FOR_EXPANDS_ARN = "PuppetOrgRoleForExpandsArn"