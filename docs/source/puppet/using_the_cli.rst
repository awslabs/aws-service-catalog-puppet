Using the CLI
=============

The following utils will help you manage your AWS Accounts when using ServiceCatalog-Puppet:


reset-provisioned-product-owner
-------------------------------

.. note::

    This was added in version 0.19.0

You can use the ``servicecatalog-puppet`` cli to update the Service Catalog Puppet managed provisioned product owner
for each provisioned product across all of your accounts:

.. code-block:: bash

    servicecatalog-puppet reset-provisioned-product-owner <path_to_expanded_manifest>

Will call the following function for each provisioned product you have:

.. code-block:: python

    service_catalog.update_provisioned_product_properties(
        ProvisionedProductId=provisioned_product_id,
        ProvisionedProductProperties={
            'OWNER': f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole"
        }
    )


add-to-accounts
---------------

.. note::

    This was added in version 0.18.0

You can use the ``servicecatalog-puppet`` cli to see add an account or ou to your accounts list:

.. code-block:: bash

    servicecatalog-puppet add-to-accounts <path_to_file_containing_account_or_ou>

The file containing the account or ou should be structured like this:

.. code-block:: yaml

    account_id: '<AccountID>'
    default_region: eu-west-1
    name: '<AccountID>'
    regions_enabled:
      - eu-west-1
      - eu-west-2
    tags:
      - type:prod
      - partition:eu
      - scope:pci


remove-from-accounts
--------------------

.. note::

    This was added in version 0.18.0

You can use the ``servicecatalog-puppet`` cli to remove an account or ou to your accounts list:

.. code-block:: bash

    servicecatalog-puppet remove-from-accounts <account_id_or_ou_id_or_ou_path>

The library will look for the given account id, ou id or ou path and remove it, if found.  If it is missing an exception
will be raised.


add-to-launches
---------------

.. note::

    This was added in version 0.18.0

You can use the ``servicecatalog-puppet`` cli to see add a launch to your launches list:

.. code-block:: bash

    servicecatalog-puppet add-to-launches <launch-name-to-add> <path_to_file_containing_launch>

The file containing the launch should be structured like this:

.. code-block:: yaml

    portfolio: example-simple-central-it-team-portfolio
    product: aws-iam-assume-roles-spoke
    version: v1
    parameters:
      SecurityAccountId:
        default: '<AccountID>'
    deploy_to:
      tags:
        - regions: default_region
          tag: type:prod


remove-from-launches
--------------------

.. note::

    This was added in version 0.18.0

You can use the ``servicecatalog-puppet`` cli to see remove a launch from your launches list:

.. code-block:: bash

    servicecatalog-puppet remove-from-launches <launch-name-to-remove>


dry-run
-------

.. note::

    This was added in version 0.8.0

You can use the ``servicecatalog-puppet`` cli to see the effect of your next pipeline run before it happens

.. code-block:: bash

    servicecatalog-puppet dry-run ServiceCatalogPuppet/manifest.yaml

You must specify the path to the manifest file you want to add execute a dry run on.


import-product-set
------------------

.. note::

    This was added in version 0.8.0

You can use the ``servicecatalog-puppet`` cli to import products from the aws-service-catalog-products shared repo.

This will update your manifest file.

.. code-block:: bash

    servicecatalog-puppet import-product-set ServiceCatalogPuppet/manifest.yaml aws-iam central-it-team-portfolio

You must specify the path to the manifest file you want to add the product set to, the name of the product set and the name
of the portfolio where was added.


list-resources
--------------

.. note::

    This was added in version 0.7.0

You can use the ``servicecatalog-puppet`` cli to list all the resources that will be created to bootstrap the framework

.. code-block:: bash

    servicecatalog-puppet list-resources


Will return the following markdown:

.. code-block:: bash

    # Framework resources
    ## SSM Parameters used
    - /servicecatalog-puppet/config
    ## Resources for stack: servicecatalog-puppet-org-master
    ┌─────────────────────────┬─────────────────────┬───────────────────────────────────────────┐
    │ Logical Name            │ Resource Type       │ Name                                      │
    ├─────────────────────────┼─────────────────────┼───────────────────────────────────────────┤
    │ Param                   │ AWS::SSM::Parameter │ service-catalog-puppet-org-master-version │
    │ PuppetOrgRoleForExpands │ AWS::IAM::Role      │ PuppetOrgRoleForExpands                   │
    └─────────────────────────┴─────────────────────┴───────────────────────────────────────────┘
    ## Resources for stack: servicecatalog-puppet-regional
    ┌────────────────────────┬─────────────────────┬────────────────────────────────────────────────────────────────────────┐
    │ Logical Name           │ Resource Type       │ Name                                                                   │
    ├────────────────────────┼─────────────────────┼────────────────────────────────────────────────────────────────────────┤
    │ DefaultRegionParam     │ AWS::SSM::Parameter │ /servicecatalog-puppet/home-region                                     │
    │ Param                  │ AWS::SSM::Parameter │ service-catalog-puppet-regional-version                                │
    │ PipelineArtifactBucket │ AWS::S3::Bucket     │ Fn::Sub: sc-puppet-pipeline-artifacts-${AWS::AccountId}-${AWS::Region} │
    │                        │                     │                                                                        │
    │ RegionalProductTopic   │ AWS::SNS::Topic     │ servicecatalog-puppet-cloudformation-regional-events                   │
    └────────────────────────┴─────────────────────┴────────────────────────────────────────────────────────────────────────┘
    ## Resources for stack: servicecatalog-puppet-spoke
    ┌──────────────┬─────────────────────┬──────────────────────────────────────┐
    │ Logical Name │ Resource Type       │ Name                                 │
    ├──────────────┼─────────────────────┼──────────────────────────────────────┤
    │ Param        │ AWS::SSM::Parameter │ service-catalog-puppet-spoke-version │
    │ PuppetRole   │ AWS::IAM::Role      │ PuppetRole                           │
    └──────────────┴─────────────────────┴──────────────────────────────────────┘
    ## Resources for stack: servicecatalog-puppet
    ┌─────────────────────────────────┬─────────────────────────────┬─────────────────────────────────────────────┐
    │ Logical Name                    │ Resource Type               │ Name                                        │
    ├─────────────────────────────────┼─────────────────────────────┼─────────────────────────────────────────────┤
    │ Param                           │ AWS::SSM::Parameter         │ service-catalog-puppet-version              │
    │ ShareAcceptFunctionRole         │ AWS::IAM::Role              │ ShareAcceptFunctionRole                     │
    │ ProvisioningRole                │ AWS::IAM::Role              │ PuppetProvisioningRole                      │
    │ CloudFormationDeployRole        │ AWS::IAM::Role              │ CloudFormationDeployRole                    │
    │ PipelineRole                    │ AWS::IAM::Role              │ PuppetCodePipelineRole                      │
    │ SourceRole                      │ AWS::IAM::Role              │ PuppetSourceRole                            │
    │ CodeRepo                        │ AWS::CodeCommit::Repository │ ServiceCatalogPuppet                        │
    │ Pipeline                        │ AWS::CodePipeline::Pipeline │ Fn::Sub: ${AWS::StackName}-pipeline         │
    │                                 │                             │                                             │
    │ GenerateRole                    │ AWS::IAM::Role              │ PuppetGenerateRole                          │
    │ DeployRole                      │ AWS::IAM::Role              │ PuppetDeployRole                            │
    │ GenerateSharesProject           │ AWS::CodeBuild::Project     │ servicecatalog-puppet-generate              │
    │ DeployProject                   │ AWS::CodeBuild::Project     │ servicecatalog-puppet-deploy                │
    │ SingleAccountRunProject         │ AWS::CodeBuild::Project     │ servicecatalog-puppet-single-account-run    │
    │ CloudFormationEventsQueue       │ AWS::SQS::Queue             │ servicecatalog-puppet-cloudformation-events │
    │ CloudFormationEventsQueuePolicy │ AWS::SQS::QueuePolicy       │ -                                           │
    └─────────────────────────────────┴─────────────────────────────┴─────────────────────────────────────────────┘

    n.b. AWS::StackName evaluates to servicecatalog-puppet


run
---

.. note::

    This was added in version 0.3.0

The run command will run the main AWS CodePipeline ``servicecatalog-puppet-pipeline``

.. code-block:: bash

    servicecatalog-puppet run

You can also tail the command to watch the progress of the pipeline.  It is a little underwhelming at the moment.


.. code-block:: bash

    servicecatalog-puppet run --tail


list-launches
-------------

The list-launches command can currently only be invoked on an expanded manifest.yaml file.  To
expand your manifest you must run the following:


.. code-block:: bash

    servicecatalog-puppet expand manifest.yaml

This will create a file named ``manifest-expanded.yaml in the same directory``.

You can then run ``list-launches``:

.. code-block:: bash

    servicecatalog-puppet list-launches manifest-expanded.yaml


Here is an example table produced by running the command:

.. code-block:: bash

    +--------------+-----------+------------------------------+------------------------------------------+---------------------------------+------------------+----------------+--------+-----------+
    | account_id   | region    | launch                       | portfolio                                | product                         | expected_version | actual_version | active | status    |
    +--------------+-----------+------------------------------+------------------------------------------+---------------------------------+------------------+----------------+--------+-----------+
    | 012345678901 | eu-west-1 | iam-assume-roles-spoke       | example-simple-central-it-team-portfolio | aws-iam-assume-roles-spoke      | v1               | v1             | True   | AVAILABLE |
    | 012345678901 | eu-west-1 | iam-groups-security-account  | example-simple-central-it-team-portfolio | aws-iam-groups-security-account | v1               | v1             | True   | AVAILABLE |
    +--------------+-----------+------------------------------+------------------------------------------+---------------------------------+------------------+----------------+--------+-----------+

.. note::

    This was added in version 0.15.0

You can specify the format of the output.  Currently you can choose between ``json`` and ``table``.  The default is
table.

.. code-block:: bash

    servicecatalog-puppet list-launches manifest-expanded.yaml --format json



export-puppet-pipeline-logs
---------------------------
The export-puppet-pipeline-logs takes a pipeline execution id and outputs a log file containing the AWS CloudWatch logs
for each AWS CodeBuild step within the pipeline.  This is useful for sharing these outputs when debugging:

.. code-block:: bash

    servicecatalog-puppet export-puppet-pipeline-logs qwertyui-qwer-qwer-qwer-qwertyuiopqw

.. note::

    This was added in version 0.47.0


graph
-----
The graph command takes an expanded manifest as a parameter and generates a graphviz formated graph representing the
actions the framework will perform

.. code-block:: bash

    servicecatalog-puppet graph <path_to_expanded_manifest>

.. note::

    This was added in version 0.49.0


Validate
--------
The validate command will check your manifest file is of the correct structure and it will also ensure you are not using
depends_on or deploy_to.tags that do not exist.

.. code-block:: bash

    servicecatalog-puppet validate <path_to_manifest>

.. note::

    This only works with the non expanded manifest file


export-full-puppet-stats
--------------------

.. note::

    This was added in version 0.132.0

The export-full-puppet-stats command will query the AWS CodeBuild APIs to gather the statistics for every execution of the 
project "servicecatalog-puppet-deploy". This data will be saved to the local filesystem in the chosen output format, 
for subsequent analysis via external tools.

.. code-block:: bash

    servicecatalog-puppet export-full-puppet-stats -f <output_type>

.. note::

    If using Excel to analyze the data stored in CSV format, the "X Y" chart type provides a suitable visualization of build
    duration over time.


export-singleaccount-stats
--------------------

.. note::

    This was added in version 0.132.0

The export-singleaccount-stats command will query the AWS CodeBuild APIs to gather the statistics for every execution of the 
project "servicecatalog-puppet-single-account-run". This data will be saved to the local filesystem in the chosen output format, 
for subsequent analysis via external tools.

.. code-block:: bash

    servicecatalog-puppet export-singleaccount-stats -f <output_type>

.. note::

    If using Excel to analyze the data stored in CSV format, the "X Y" chart type provides a suitable visualization of build
    duration over time.

