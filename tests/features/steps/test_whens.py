from behave import when

from servicecatalog_puppet import config, sdk

from . import constants

roles = {
    "PuppetCodePipelineRole": 'puppet_code_pipeline_role_permission_boundary',
    "SourceRolePermissionsBoundary": "source_role_permissions_boundary",
    "PuppetGenerateRolePermissionBoundary": "puppet_generate_role_permission_boundary",
    "PuppetDeployRolePermissionBoundary": "puppet_deploy_role_permission_boundary",
    "PuppetProvisioningRolePermissionsBoundary": "puppet_provisioning_role_permissions_boundary",
    "CloudFormationDeployRolePermissionsBoundary": "cloud_formation_deploy_role_permissions_boundary",

}


@when(u'I bootstrap a "{account_type}" account with version "{version}" and set an IAM Boundary for "{role}"')
def step_impl(context, account_type, version, role):
    if account_type == "puppet":
        args = {
            "with_manual_approvals": False
        }
        args[roles.get(role)] = constants.BOUNDARY_ARN_TO_USE
        sdk.bootstrap(**args)

    elif account_type == "spoke":
        sdk.bootstrap_spoke(
            config.get_puppet_account_id(),
            "arn:aws:iam::aws:policy/AdministratorAccess"
        )


@when(u'I bootstrap a "{account_type}" account with version "{version}"')
def step_impl(context, account_type, version):
    if account_type == "puppet":
        sdk.bootstrap(False)
    elif account_type == "spoke":
        sdk.bootstrap_spoke(
            config.get_puppet_account_id(),
            "arn:aws:iam::aws:policy/AdministratorAccess"
        )
