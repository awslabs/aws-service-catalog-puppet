Designing your manifest
=======================

Purpose of the manifest file
----------------------------
The manifest file is there to describe what you want to provision and into which accounts you want to provision products
into.  It is possible to use AWS Organizations to make your manifest file more concise and easier to work with but the
premise is the same - it is just a list of accounts and AWS Service Catalog products.


Sections of the manifest file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There are three sections to a manifest file - the global parameters, the accounts list and the launches.  Each of the 
three are described in the following sections.

Parameters
##########


It is possible to specify global parameters that should be used when provisioning your AWS Service Catalog Products.
You can set the value to an explicit value or you can set the value to the result of a function call - using funcation 
calls to set parameter values is known as using a macro.

Here is an example of a simple global parameter:

.. code-block:: yaml

    schema: puppet-2019-04-01

    parameters:
        CloudTrailLoggingBucketName:
          default: cloudtrail-logs-for-aws

It is possible to also specify a parameter at the account level:

.. code-block:: yaml

    accounts:
      - account_id: '<YOUR_ACCOUNT_ID>'
        name: '<YOUR_ACCOUNT_NAME>'
        default_region: eu-west-1
        regions_enabled:
          - eu-west-1
          - eu-west-1
        tags:
          - type:prod
          - partition:eu
          - scope:pci
        parameters:
          RoleName:
            default: DevAdmin
          Path:
            default: /human-roles/


And finally you specify parameters at the launch level:

.. code-block:: yaml

    launches:
      account-iam-for-prod:
        portfolio: demo-central-it-team-portfolio
        product: account-iam
        version: v1
        parameters:
          RoleName:
            default: DevAdmin
          Path:
            default: /human-roles/
        deploy_to:
          tags:
            - tag: type:prod
              regions: default_region


Whenever Puppet provisions a product it checks the parameters for the product.  If it sees the name match one of the 
parameter values it will use it.  In order to avoid clashes with parameter names we recommend using descriptive names 
like in the example - using the parameter names like ``BucketName`` will lead you into trouble pretty quickly.

The order of precedence for parameters is account level parameters override all others and launch level parameters 
override global.

Retrieving AWS SSM Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This was added in version 0.0.33

You can retrieve parameter values from SSM.  Here is an an example:

.. code-block:: yaml

    schema: puppet-2019-04-01

    parameters:
        CentralLoggingBucketName:
          ssm:
            name: central-logging-bucket-name


You can get a different value for each region:

.. code-block:: yaml

    schema: puppet-2019-04-01

    parameters:
        CentralLoggingBucketName:
          ssm:
            name: central-logging-bucket-name
            region: eu-west-1


Setting AWS SSM Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This was added in version 0.0.34

You can set the value of an SSM Parameter to the output of a CloudFormation stack output:

.. code-block:: yaml

      account-iam-sysops:
        portfolio: demo-central-it-team-portfolio
        product: account-iam
        version: v1
        parameters:
          Path:
            default: /human-roles/
          RoleName:
            default: SysOps
        deploy_to:
          tags:
          - regions: default_region
            tag: type:prod
        outputs:
          ssm:
            -  param_name: account-iam-sysops-role-arn
               stack_output: RoleArn

  
The example above will provision the product ``account-iam`` into an account.  Once the stack has been completed it
will get the value of the output named ``RoleArn`` of the CloudFormation stack and insert it into SSM within the default
region using a parameter name of ``account-iam-sysops-role-arn``

You can also set override which region the output is read from and which region the SSM parameter is written to:

.. code-block:: yaml

  account-iam-sysops:
    portfolio: demo-central-it-team-portfolio
    product: account-iam
    version: v1
    parameters:
      Path:
        default: /human-roles/
      RoleName:
        default: SysOps
    deploy_to:
      tags:
      - regions: default_region
        tag: type:prod
    outputs:
      ssm:
        -  param_name: account-iam-sysops-role-arn
           stack_output: RoleArn
           region: us-east-1


.. note::

    There is currently no capability of reading a value from a CloudFormation stack from one region and setting an SSM param in another.


Macros
~~~~~~

You can also use a macro to set the value of a parameter.  It works in the same way as a normal parameter except it 
executes a function to get the value first.  Here is an an example:

.. code-block:: yaml

    schema: puppet-2019-04-01

    parameters:
        AllAccountIds:
          macro:
            method: get_accounts_for_path
            args: /


At the moment there are the following macros supported:

.. code-block:: yaml

    +------------------------+------------------------------+----------------------------------------------+
    | macro method name      | args                         | description                                  |
    +========================+==============================+==============================================+
    | get_accounts_for_path  | ou path to get accounts for  | Returns a comma seperated list of account ids|
    +------------------------+------------------------------+----------------------------------------------+


Accounts
########

With the accounts section, you can describe your AWS accounts.  You can set a default region, the enabled regions and 
you can tag your accounts.  This metadata describing your account is used to determine which packages get deployed into
your accounts.

Setting a default region
~~~~~~~~~~~~~~~~~~~~~~~~

Within your account you may have a _home_ or a default region.  This may be the closest region to the team using the 
account.  You use ``default_region`` when describing your account and then you can use ``default_region`` again as a
target when you specify your product launches - the product will be provisioned into the region specified.

Here is an example with a ``default_region`` set to ``us-east-1``:

.. code-block:: yaml

    schema: puppet-2019-04-01

    accounts:
      - account_id: '<YOUR_ACCOUNT_ID>'
        name: '<YOUR_ACCOUNT_NAME>'
        default_region: us-east-1
        regions_enabled:
          - us-east-1
          - us-west-2
        tags:
          - type:prod
          - partition:us
          - scope:pci


.. note::

    Please note ``default_region`` can only be a string - not a list.

Setting enabled regions
~~~~~~~~~~~~~~~~~~~~~~~

You may chose not to use every region within your AWS Account.  When describing an AWS account you can specify which 
regions are enabled for an account using ``regions_enabled``.

Here is an example with ``regions_enabled`` set to ``us-east-1 and us-west-2``:

.. code-block:: yaml

    schema: puppet-2019-04-01

    accounts:
      - account_id: '<YOUR_ACCOUNT_ID>'
        name: '<YOUR_ACCOUNT_NAME>'
        default_region: us-east-1
        regions_enabled:
          - us-east-1
          - us-west-2
        tags:
          - type:prod
          - partition:us
          - scope:pci


.. note::

    Please note ``regions_enabled`` can only be a list of strings - not a single string


Setting tags
~~~~~~~~~~~~

You can describe your account using tags.  Tags are specified using a list of strings.  We recommend using namespaces 
for your tags, adding an extra dimension to them.  If you choose to do this you can use a colon to split name and values.

Here is an example with namespaced tags:
   
.. code-block:: yaml

    schema: puppet-2019-04-01

    accounts:
      - account_id: '<YOUR_ACCOUNT_ID>'
        name: '<YOUR_ACCOUNT_NAME>'
        default_region: us-east-1
        regions_enabled:
          - us-east-1
          - us-west-2
        tags:
          - type:prod
          - partition:us
          - scope:pci


In this example there the following tags:
- namespace of type and value of prod
- namespace of partition and value of us
- namespace of scope and value of pci.

The goal of tags is to provide a classification for your accounts that can be used to a deployment time.  

Using an OU id or path (integration with AWS Organizations)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This was added in version 0.0.18

When specifying an account you can use short hand notation of ``ou`` instead of ``account_id`` to build out a list
of accounts with the same properties.

For example you can use an AWS Organizations path:

.. code-block:: yaml

    schema: puppet-2019-04-01

    accounts:
      - ou: /prod
        name: '<CHOOSE A NAME FOR YOUR ACCOUNTS LIST>'
        default_region: us-east-1
        regions_enabled:
          - us-east-1
          - us-west-2
        tags:
          - type:prod
          - partition:us
          - scope:pci


The framework will get a list of all AWS accounts within the ``/prod`` Organizational unit and expand your manifest to
look like the following  (assuming accounts 0123456789010 and 0109876543210 are the only accountss within ``/prod``):

.. code-block:: yaml

    schema: puppet-2019-04-01

    accounts:
      - account_id: 0123456789010
        name: '<YOUR_ACCOUNT_NAME>'
        default_region: us-east-1
        regions_enabled:
          - us-east-1
          - us-west-2
        tags:
          - type:prod
          - partition:us
          - scope:pci
      - account_id: 0109876543210
        name: '<YOUR_ACCOUNT_NAME>'
        default_region: us-east-1
        regions_enabled:
          - us-east-1
          - us-west-2
        tags:
          - type:prod
          - partition:us
          - scope:pci


Launches
########

Launches allow you to decide which products get provisioned into each account.  You link product launches to accounts 
using tags or explicit account ids and you can set which regions the products are launched into.

Timeouts
~~~~~~~~

.. note::

    This was added in version 0.1.14

If you are worried that a launch may fail and take a long time to fail you can set a timeout ``timeoutInSeconds``:

.. code-block:: yaml

    schema: puppet-2019-04-01

    launches:
      account-iam-for-prod:
        portfolio: example-simple-central-it-team-portfolio
        product: account-iam
        timeoutInSeconds: 10
        version: v1
        deploy_to:
          tags:
            - tag: type:prod
              regions: default_region



Tag based launches
~~~~~~~~~~~~~~~~~~

You can specify a launch to occur using ``tags`` in the ``deploy_to`` section of a launch.

Here is an example, it deploys a ``v1`` of a product named ``account-iam`` from the portfolio
``example-simple-central-it-team-portfolio`` into into the ``default_region`` of all accounts tagged ``type:prod``:

.. code-block:: yaml

    schema: puppet-2019-04-01

    launches:
      account-iam-for-prod:
        portfolio: example-simple-central-it-team-portfolio
        product: account-iam
        version: v1
        deploy_to:
          tags:
            - tag: type:prod
              regions: default_region


When you specify more than one tag entry in deploy_to->tags the framework will interpret this as an or so the following
snippet will provision ``v1`` of ``account-iam`` to all accounts tagged ``type:prod`` or ``type:dev``:

.. code-block:: yaml

    schema: puppet-2019-04-01

    launches:
      account-iam-for-prod:
        portfolio: example-simple-central-it-team-portfolio
        product: account-iam
        version: v1
        deploy_to:
          tags:
            - tag: type:prod
              regions: default_region
            - tag: type:dev
              regions: default_region



Account based launches
~~~~~~~~~~~~~~~~~~~~~~

You can also specify a launch to occur explicity in an account by using the ``accounts`` section in the
``deploy_to`` section of a launch.

Here is an example, it deploys a ``v1`` of a product named ``account-iam`` from the portfolio
``example-simple-central-it-team-portfolio`` into into the ``default_region`` of the accounts ``0123456789010``:

.. code-block:: yaml

    schema: puppet-2019-04-01

    launches:
      account-iam-for-prod:
        portfolio: example-simple-central-it-team-portfolio
        product: account-iam
        version: v1
        deploy_to:
          accounts:
            - account_id: '0123456789010'
              regions: default_region


Choosing which regions to provision into
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When writing your launches you can choose which regions you provision into.

The valid values for regions are:

- ``enabled`` - this will deploy to each enabled region for the account
- ``regions_enabled`` - this will deploy to each enabled region for the account
- ``default_region`` - this will deploy to the default region specified for the account
- ``all`` - this will deploy to all regions enabled in your config (whilst setting up Puppet)
- list of AWS regions - you can type in a list of AWS regions (each region selected should be present in your config)


Dependencies between launches
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Where possible we recommend building launches to be independent.  However, there are cases where you may need to setup a
hub account before setting up a spoke or there may be times you are using AWS Lambda to back AWS CloudFormation custom 
resources.  In these examples it would be beneficial to be able to say deploy launch x and then launch y.  To achieve this
You can use ``depends_on`` within your launch like so:

.. code-block:: yaml

    launches:
      account-vending-account-creation:
        portfolio: demo-central-it-team-portfolio
        product: account-vending-account-creation
        version: v1
        depends_on:
          - account-vending-account-bootstrap-shared
          - account-vending-account-creation-shared
        deploy_to:
          tags:
            - tag: scope:puppet-hub
              regions: default_region

      account-vending-account-bootstrap-shared:
        portfolio: demo-central-it-team-portfolio
        product: account-vending-account-bootstrap-shared
        version: v1
        deploy_to:
          tags:
            - tag: scope:puppet-hub
              regions: default_region

      account-vending-account-creation-shared:
        portfolio: demo-central-it-team-portfolio
        product: account-vending-account-creation-shared
        version: v1
        deploy_to:
          tags:
            - tag: scope:puppet-hub
              regions: default_region


In this example the framework will deploy ``account-vending-account-creation`` only when
``account-vending-account-bootstrap-shared`` and ``account-vending-account-creation-shared`` have been attempted.


Termination of products
~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This was added in version 0.1.11

To terminate the provisioned product from a spoke account (which will delete the resources deployed) you can change
the status of the launch using the ``status`` keyword:

.. code-block:: yaml

    launches:
      account-vending-account-creation:
        portfolio: demo-central-it-team-portfolio
        product: account-vending-account-creation
        version: v1
        status: terminated
        deploy_to:
          tags:
            - tag: scope:puppet-hub
              regions: default_region


When you mark a launch as terminated and run your pipeline the resources will be deleted and you can then remove the 
launch from your manifest.  Leaving it in will not cause any errors but will result in your pipeline running time to be 
longer than it needs to be.

Please note, when mark your launch as ``terminated`` it cannot have dependencies, parameters or outputs.  Leaving
these in will cause the termination action to fail.

.. note::

    When you set status to terminated you must remove your depends_on and parameters for it to work.

.. warning::

    Since 0.1.16, terminating a product will also remove any SSM Parameters you created for it via the manifest.yaml


Managing large manifests or working in teams (multiple manifest files)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This was added in version 0.71.0

If you have a large manifest file or are working in a team you may find it difficult managing changes occurring to your
manifest file.  You may find yourself having a lot of merge conflicts.  To resolve this you can split your manifest file
into smaller pieces.  You can specify launches in a launch directory within your ServiceCatalogPuppet repository:

.. code-block:: bash

    ✗ tree ServiceCatalogPuppet
    ServiceCatalogPuppet
    ├── launches
    │   └── launches-for-team-a.yaml
    ├── manifest.yaml

The file (in this example launches-for-team-a.yaml) should be a list of launches:

.. code-block:: bash

    ✗ cat launches-for-team-a.yaml
    account-vending-account-creation:
        portfolio: demo-central-it-team-portfolio
        product: account-vending-account-creation
        version: v1
        depends_on:
          - account-vending-account-bootstrap-shared
          - account-vending-account-creation-shared
        deploy_to:
          tags:
            - tag: scope:puppet-hub
              regions: default_region

    account-vending-account-bootstrap-shared:
        portfolio: demo-central-it-team-portfolio
        product: account-vending-account-bootstrap-shared
        version: v1
        deploy_to:
          tags:
            - tag: scope:puppet-hub
              regions: default_region



The framework will load the manifest.yaml and *overwrite* any launches with ones defined in files from the launches
directory.  The framework will not warn you of any overrides.

You can also specify parameters and spoke-local-portfolios in directories too.  When doing so, the files should contain
lists of parameters or spoke-local-portfolios and should not be a dictionary.

.. code-block:: bash

    ✗ tree ServiceCatalogPuppet
    ServiceCatalogPuppet
    ├── parameters
    │   └── parameters-for-team-a.yaml
    ├── spoke-local-portfolios
    │   └── spoke-local-portfolios-for-team-a.yaml
    ├── manifest.yaml

The names of the file within the launches, parameters and spoke-local-portfolios are ignored.

You can also declare other manifest files in a manifests directory:

.. code-block:: bash

    ✗ tree ServiceCatalogPuppet
    ServiceCatalogPuppet
    ├── manifests
    │   └── manifest-for-team-a.yaml
    │   └── manifest-for-networking.yaml
    │   └── manifest-for-governance.yaml

When you write a manifest file in the manifests directory the accounts section is ignored - you can only specify
launches, parameters and spoke-local-portfolios.


Managing large manifests or working across multiple environments (external versions / properties files)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This was added in version 0.76.0

If you are using puppet to manage multiple environments you may find it easier to keep the versions of your launches in
properties files instead of the manifest.yaml files.  To do this you create a file named manifest.properties in the same
directory as your manifest.yaml file.  Within this file you can specify the following:

.. code-block:: ini

    [launches]
    IAM-1.version = v50

This will set the version for the launch with the name IAM-1 to v50.

Please note this will overwrite the values specified in the manifest.yaml files with no warning.

If you are using multiple instances of puppet you can also create a file named manifest-<puppet-account-id>.properties.
Values in this file will overwrite all other values making the order of reading:

1.  manifest.yaml
2.  files in manifests/*.yaml
3.  manifest.properties
4.  manifest-<puppet-account-id>.properties