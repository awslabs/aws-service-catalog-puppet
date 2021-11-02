Intrinsic functions
===================

-------------------------------------
What are intrinsic functions
-------------------------------------

.. note::

    The first intrinsic function was added in version 0.115.0

Intrinsic functions allow you to specify a token in the manifest.yaml file and have it replaced with a value generated
by the tools at runtime.  The aim of them is to make your manifest.yaml file more portable across environments and to
make your life managing the manifest.yaml file easier.


PuppetAccountId
---------------

.. note::

    This was added in version 0.115.0

You can use the token ${AWS::PuppetAccountId} anywhere in your manifest files.  When you do so it will be replaced
with the puppet account id you are using.  This replacement occurs in the expand phase and the deploy phase is unaware
of the notation.  When using the PuppetAccountId intrinsic function we recommend ensuring it is string by surrounding
it in double quotes - this avoids issues where the account id may be passed as a number later on.

Here is an example usage of it in the parameters section:

.. code-block:: yaml

    schema: puppet-2019-04-01
    parameters:
      PuppetAccountId1:
        default: "${AWS::PuppetAccountId}"
      OrganizationAccountAccessRole:
        default: OrganizationAccountAccessRole

And here is an example in a stack:

.. code-block:: yaml

    stacks:
      networking-stack:
        name: networking-stack
        version: v1
        parameters:
          PuppetAccountId:
            default: "${AWS::PuppetAccountId}"
        deploy_to:
          tags:
            - regions: default_region
              tag: role:puppethub
