Frequently asked Questions (FAQ)
================================


.. contents:: :local:


PuppetRole has been recreated
-----------------------------
Q. My PuppetRole has been recreated and now I cannot perform updates to provisioned products.  What should I do?

A. You will need to follow these steps:

- Delete the AWS Cloudformation Stacks named ``servicecatalog-puppet-shares``.  There will be one in each region you operate in.  you can use the utility `delete-stack-from-all-regions <https://aws-service-catalog-factory.readthedocs.io/en/latest/factory/using_the_cli.html#delete-stack-from-all-regions>`_ to help
- Run the puppet pipeline again
- Run the cli command `reset-provisioned-product-owner <https://aws-service-catalog-factory.readthedocs.io/en/latest/factory/using_the_cli.html#reset-provisioned-product-owner>`_ on your expanded manifest file.


How do I enable OpsCenter support
---------------------------------
Q. How do I enable OpsCenter support?

A.  You will need to be running at least version 0.35.0.  You can check your version by running the version cli command.
If it is below 0.35.0 you will need to upgrade.  Once you are running the correct version you will been to update your
config file to include:

.. code-block:: yaml

    should_forward_failures_to_opscenter: true


Your file should look like the following:

.. code-block:: yaml

    regions: [
      'eu-west-1',
      'eu-west-2',
      'eu-west-3'
    ]
    should_forward_failures_to_opscenter: true

Once you have made the change you will need to upload your config again:

.. code-block:: bash

    servicecatalog-puppet upload-config config.yaml


How can I exclude an account or a sub Organizational unit from an expand
------------------------------------------------------------------------
Q. How can I exclude an account or a sub Organizational unit from an expand?

A. You can use an exclude attribute within your ou block:

.. code-block:: yaml

      - ou: /
        default_region: eu-west-1
        name: '665532578041'
        regions_enabled:
          - eu-west-1
          - eu-west-2
        tags:
          - type:spoke
          - partition:eu
          - scope:pci
        exclude:
          accounts:
            - 0123456789010
          ous:
            - '/hub'

Excludes can include accounts or ous.  Please note the ous work recursively so the example above to create a list of
accounts that is all accounts in the organization excluding account ``0123456789010`` and excluding all accounts from
``/hub`` and all of ``/hub`` sub organizations

.. note::

    exclude was added in version 0.53.0


How can I add tags or regions or change the default region of a single account within an OU
-------------------------------------------------------------------------------------------
Q. How can I add tags or regions or change the default region of a single account within an OU?

A. You can continue using the OU notation to describe the group of accounts the account you want to customise sits in:

.. code-block:: yaml

      - ou: /eu-dev
        name: 'eu-dev'
        default_region: eu-west-1
        regions_enabled:
          - eu-west-1
          - eu-west-2
        tags:
          - type:spoke
          - partition:eu

You can then add a tag to the account by adding the following to your manifest:

.. code-block:: yaml

      - account_id: '665532578041'
        name: '665532578041'
        append:
          tags:
            - scope:pci

This means all accounts in the eu-dev OU will have the following tags:

.. code-block:: yaml

    - type:spoke
    - partition:eu

and account '665532578041' will have the following tags:

.. code-block:: yaml

    - type:spoke
    - partition:eu
    - scope:pci

Instead of using append you can also use overwrite.  Using overwrite would replace the tags in the example above.

When using append you can specify tags and regions_enabled to be appended.

When using overwrite you can specify default_region, tags and regions_enabled to be overwritten.

.. note::

    exclude was added in version 0.63.0
