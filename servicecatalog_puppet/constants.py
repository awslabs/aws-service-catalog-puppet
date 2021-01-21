import os

PREFIX = "SC-P--"
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

PROVISIONED = "provisioned"
TERMINATED = "terminated"

DEFAULT_TIMEOUT = 0
LAUNCHES = "launches"
SPOKE_LOCAL_PORTFOLIOS = "spoke-local-portfolios"

RESULTS_DIRECTORY = "results"

NO_CHANGE = "NO_CHANGE"
CHANGE = "CHANGE"

EVENT_BUS_NAME = "servicecatalog-puppet-event-bus"
EVENT_BUS_IN_SPOKE_NAME = "servicecatalog-puppet-spoke-event-bus"
SERVICE_CATALOG_PUPPET_EVENT_SOURCE = "servicecatalog-puppet"
SERVICE_CATALOG_PUPPET_OPS_CENTER_SOURCE = "servicecatalog-puppet"

HOME_REGION = os.environ.get(
    "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "eu-west-1")
)

EVENTBRIDGE_MAX_EVENTS_PER_CALL = 10

SPOKE_VERSION_SSM_PARAM_NAME = "service-catalog-puppet-spoke-version"
PUPPET_VERSION_SSM_PARAM_NAME = "service-catalog-puppet-version"

SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED = "shared"
SPOKE_LOCAL_PORTFOLIO_STATUS_TERMINATED = "terminated"

EXECUTION_MODE_ASYNC = "async"
EXECUTION_MODE_HUB = "hub"
EXECUTION_MODE_SPOKE = "spoke"
EXECUTION_MODE_DEFAULT = EXECUTION_MODE_HUB
EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME = "servicecatalog-puppet-deploy-in-spoke"


SHARING_MODE_ACCOUNT = "ACCOUNT"
SHARING_MODE_AWS_ORGANIZATIONS = "AWS_ORGANIZATIONS"
SHARING_MODE_DEFAULT = SHARING_MODE_ACCOUNT

PARTITION_DEFAULT = "aws"
PARTITION_ENVIRONMENTAL_VARIABLE_NAME = "PARTITION"
PARTITION_SSM_PARAMETER_VARIABLE_NAME = "/servicecatalog-puppet/partition"

PUPPET_ROLE_NAME_DEFAULT = "PuppetRole"
PUPPET_ROLE_NAME_ENVIRONMENTAL_VARIABLE_NAME = "PUPPET_ROLE_NAME"
PUPPET_ROLE_NAME_SSM_PARAMETER_VARIABLE_NAME = "/servicecatalog-puppet/puppet-role/name"

PUPPET_ROLE_PATH_DEFAULT = "/servicecatalog-puppet/"
PUPPET_ROLE_PATH_ENVIRONMENTAL_VARIABLE_NAME = "PUPPET_ROLE_PATH"
PUPPET_ROLE_PATH_SSM_PARAMETER_VARIABLE_NAME = "/servicecatalog-puppet/puppet-role/path"


DEPLOY_ENVIRONMENT_COMPUTE_TYPE_DEFAULT = "BUILD_GENERAL1_SMALL"


CONFIG_IS_CACHING_ENABLED = "CONFIG_IS_CACHING_ENABLED"


START_SHARED_SCHEDULER_COMMAND = "luigid --background --pidfile luigi.pid --logdir results/logs --state-path results/state"
