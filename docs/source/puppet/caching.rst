Caching
=======

-------------------------------------
What is caching and how does it work?
-------------------------------------

.. note::

    This was added in version 0.84.0

This framework uses the python library Luigi to generate and execute its workflow and to handle dependencies.  This
framework generates a series of tasks that will provision products, share portfolios and execute lambda functions.  Luigi
then starts workers that will consume the tasks and report back on their status.

The tasks we generate are fairly fine grained to enabled better concurrency and to make use of Luigi's ability to cache
task instances so that the exact same task will not be executed more than once.

Some of these tasks we generate in this framework should never need to be executed more than once - for example getting
the provisioning parameters for a specific AWS Service Catalog provisioning artifact.

When Luigi runs a task it generates a target which is a file containing the result of the task.  Each time Luigi runs it
checks to see if the target exists already - if it does then it will not rerun the task.

You can enable the caching of the following tasks:
- DeleteCloudFormationStackTask
- EnsureEventBridgeEventBusTask
- BootstrapSpokeAsTask
- CreateLaunchRoleConstraintsForPortfolio
- RequestPolicyTask
- SharePortfolioTask
- ShareAndAcceptPortfolioTask
- CreateAssociationsInPythonForPortfolioTask
- CreateShareForAccountLaunchRegion
- DisassociateProductFromPortfolio
- DisassociateProductsFromPortfolio
- DeleteLocalPortfolio
- DeletePortfolioShare
- DeletePortfolio
- ProvisioningArtifactParametersTask
- ResetProvisionedProductOwnerTask
- RunDeployInSpokeTask
- LaunchInSpokeTask

.. warning::

    Since 0.84.0 this feature has only been tested when execution mode is hub.  If you encounter any issues in any other
    mode please raise an issue.  Support for other execution modes will be added shortly.


-------------------------------------------
What should I do if I think I see an issue?
-------------------------------------------
Please check through the github issues to check if your issue has been raised already.  If not, please raise a new
github issue so progress can be tracked.

--------------------------
How can I empty the cache?
--------------------------

The cache is copied over to AWS S3 after every run and copied back before each future run.  You can delete the cache
should you want to empty it:

.. code:: shell

    aws s3 rm --recursive s3://sc-puppet-caching-bucket-${PUPPET_ACCOUNT_ID}-${AWS_REGION}/output

It is not recommended to delete specific files from the cache as there is a complex relationship between the files due
to the task dependencies.

---------------------
How do I enable this?
---------------------

In order to use this feature you will need to enable caching using the CLI:

.. code:: shell

    servicecatalog-puppet set-config-value is_caching_enabled True

Following that you will need to bootstrap using the settings you previously used:

.. code:: shell

    servicecatalog-puppet bootstrap ..... ...... ......


----------------------
How do I disable this?
----------------------

In order to use disable feature you will need to disable caching using the CLI:

.. code:: shell

    servicecatalog-puppet set-config-value is_caching_enabled False

Following that you will need to bootstrap using the settings you previously used:

.. code:: shell

    servicecatalog-puppet bootstrap ..... ...... ......
