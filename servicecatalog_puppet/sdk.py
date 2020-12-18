# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import core


def run(what="puppet", wait_for_completion=False):
    """
    Run something

    :param what: what should be run.  The only parameter that will work is ``puppet``
    :param wait_for_completion: Whether the command should wait for the completion of the pipeline before it returns
    """
    core.run(what, wait_for_completion)


def add_to_accounts(account_or_ou):
    """
    Add the parameter to the account list of the manifest file

    :param account_or_ou: A dict describing the the account or the ou to be added
    """
    core.add_to_accounts(account_or_ou)


def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    """
    remove the given ``account_id_or_ou_id_or_ou_path`` from the account list

    :param account_id_or_ou_id_or_ou_path: the value can be an account_id, ou_id or an ou_path.  It should be present \
    in the accounts list within the manifest file or an error is generated
    """
    core.remove_from_accounts(account_id_or_ou_id_or_ou_path)


def add_to_launches(launch_name, launch):
    """
    Add the given ``launch`` to the launches section using the given ``launch_name``

    :param launch_name: The launch name to use when adding the launch to the manifest launches
    :param launch: The dict to add to the launches
    """
    core.add_to_launches(launch_name, launch)


def remove_from_launches(launch_name):
    """
    remove the given ``launch_name`` from the launches list

    :param launch_name: The name of the launch to be removed from the launches section of the manifest file
    """
    core.remove_from_launches(launch_name)


def upload_config(config):
    """
    This function allows you to upload your configuration for puppet.  At the moment this should be a dict with an
    attribute named regions:
    regions: [
      'eu-west-3',
      'sa-east-1',
    ]

    :param config: The dict containing the configuration used for puppet
    """
    core.upload_config(config)


def bootstrap(
    with_manual_approvals,
    puppet_account_id,
    puppet_code_pipeline_role_permission_boundary="arn:aws:iam::aws:policy/AdministratorAccess",
    source_role_permissions_boundary="arn:aws:iam::aws:policy/AdministratorAccess",
    puppet_generate_role_permission_boundary="arn:aws:iam::aws:policy/AdministratorAccess",
    puppet_deploy_role_permission_boundary="arn:aws:iam::aws:policy/AdministratorAccess",
    puppet_provisioning_role_permissions_boundary="arn:aws:iam::aws:policy/AdministratorAccess",
    cloud_formation_deploy_role_permissions_boundary="arn:aws:iam::aws:policy/AdministratorAccess",
    deploy_environment_compute_type="BUILD_GENERAL1_SMALL",
    deploy_num_workers=10,
):
    """
    Bootstrap the puppet account.  This will create the AWS CodeCommit repo containing the config and it will also
    create the AWS CodePipeline that will run the solution.

    :param with_manual_approvals: Boolean to specify whether there should be manual approvals before provisioning occurs
    :param puppet_account_id: AWS Account Id for your puppet account
    :param puppet_code_pipeline_role_permission_boundary: IAM Boundary to apply to the role: PuppetCodePipelineRole
    :param source_role_permissions_boundary: IAM Boundary to apply to the role: SourceRole
    :param puppet_generate_role_permission_boundary: IAM Boundary to apply to the role: PuppetGenerateRole
    :param puppet_deploy_role_permission_boundary: IAM Boundary to apply to the role: PuppetDeployRole
    :param puppet_provisioning_role_permissions_boundary: IAM Boundary to apply to the role: PuppetProvisioningRole
    :param cloud_formation_deploy_role_permissions_boundary: IAM Boundary to apply to the role: CloudFormationDeployRole
    :param deploy_environment_compute_type: The AWS CodeBuild Environment Compute Type
    :param deploy_num_workers: Number of workers that should be used when running a deploy
    """

    core.bootstrap(
        with_manual_approvals,
        puppet_account_id,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
        deploy_environment_compute_type,
        deploy_num_workers,
    )


def bootstrap_spoke(puppet_account_id, permission_boundary):
    """
    Bootstrap a spoke so that is can be used by the puppet account to share portfolios and provision products.  This
    must be run in the spoke account.

    :param puppet_account_id: this is the account id where you have installed aws-service-catalog-puppet
    :param permission_boundary: the iam boundary to apply to the puppetrole in the spoke account
    """
    core.bootstrap_spoke(puppet_account_id, permission_boundary)


def bootstrap_spoke_as(
    puppet_account_id,
    iam_role_arns,
    permission_boundary,
    puppet_role_name="PuppetRole",
    puppet_role_path="/servicecatalog-puppet/",
):
    """
    Bootstrap a spoke so that it can be used by the puppet account to share portfolios and provision products.  This
    must be run in an account where you can assume the first ARN in the iam_role_arns list.

    :param puppet_account_id: this is the account id where you have installed aws-service-catalog-puppet
    :param iam_role_arns: this is a list of ARNs the function will assume (in order) before bootstrapping.  The final \
    ARN in the list should be the ARN of the spoke you want to bootstrap.
    :param permission_boundary: the iam boundary to apply to the puppetrole in the spoke account
    """
    core.bootstrap_spoke_as(
        puppet_account_id,
        iam_role_arns,
        permission_boundary,
        puppet_role_name,
        puppet_role_path,
    )


def bootstrap_spokes_in_ou(
    ou_path_or_id,
    role_name,
    iam_role_arns,
    permission_boundary,
    num_workers=10,
    puppet_role_name="PuppetRole",
    puppet_role_path="/servicecatalog-puppet/",
):
    """
    Bootstrap each spoke in the given path or id

    :param ou_path_or_id: This is the ou path /example or the ou id for which you want each account bootstrapped
    :param role_name: This is the name (not ARN) of the IAM role to assume in each account when bootstrapping
    :param iam_role_arns: this is a list of ARNs the function will assume (in order) before bootstrapping.  The final \
    ARN in the list should be the ARN of account that can assume the role_name in the accounts to bootstrap.
    :param permission_boundary: the iam boundary to apply to the puppetrole in the spoke account
    """
    core.bootstrap_spokes_in_ou(
        ou_path_or_id,
        role_name,
        iam_role_arns,
        permission_boundary,
        num_workers,
        puppet_role_name,
        puppet_role_path,
    )


def uninstall(puppet_account_id):
    """
    Delete the resources created during the bootstrap process.  AWS Service Catalog portfolios and their configurations
    are not modified during this call

    :param puppet_account_id: AWS Account Id for your puppet account
    """
    core.uninstall(puppet_account_id)


def release_spoke(puppet_account_id):
    """
    Delete the resources created during the bootstrap spoke process

    :param puppet_account_id: AWS Account Id for your puppet account
    """
    core.release_spoke(puppet_account_id)
