Execution modes
===============

What are execution modes
------------------------

Execution modes alter the way the framework runs.  When you change the value of the execution mode you change how or
where the execution will occur.

Up until version 0.76.0 this framework only supported a single execution mode - hub.  This meant there was a single
pipeline provisioning products and sharing portfolios.  This is still the default mode.  When you configure a launch
you can set the execution mode.  If you do not set it, it will default back to hub.  Read the following to understand
more about the different execution modes.


How to set the execution mode
-----------------------------

You can configure the execution mode for a launch by setting it:

.. code-block:: yaml

      IAM-1:
        portfolio: e-mandatory
        product: aws-iam-administrator-access-assumable-role-account
        version: v1
        execution: async
        parameters:
          AccountToTrust:
            default: '0123456789010'
          RoleName:
            default: 'SuperAdmin'
          Path:
            default: '/'
        deploy_to:
          tags:
            - tag: role:spokes
              regions: default_region


You can change the execution mode to any of the accepted values at any time.


Hub
---

Hub is the default.  It means all provisioning occurs in the main AWS CodeBuild project in the puppet account.  During a
hub execution the CodeBuild project will wait for each execution to complete before processing its dependents.


Async
-----

.. note::

    This was added in version 0.76.0

With async the provisioning still occurs in the CodeBuild project of the puppet account but when provisioning of
launches is running the CodeBuild project does not wait for the completion of the product provisioning.  This means you
cannot depend on a launch that is async and you cannot have outputs for an async launch.