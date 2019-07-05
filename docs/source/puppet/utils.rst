Utils
=====

The following utils will help you manage your AWS Accounts when using ServiceCatalog-Puppet:


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
