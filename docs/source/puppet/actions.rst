Actions
=======

What are actions
----------------

Actions are checks you can run that enable you to verify a condition during the provisioning of your products and sharing
of your portfolios.


Types of actions
----------------

You can create an action using AWS CodeBuild.  To do so, you create a project as you normally would.  You can create a
project by provisioning a product or you can manage this using other tools.  Once you have create a CodeBuild project
you need to add it to your manifest as an action so the framework can use it:

.. code-block:: yaml

    actions:
      ping-on-prem-host:
        type: codebuild
        project_name: ping-on-prem-host
        account_id: '0123456789010'
        region: 'eu-west-1'
        parameters:
          HOST_TO_PING:
            default: 192.168.1.2


Note, the parameter specified above.  You can also specify AWS SSM Parameters too (in the same way you specify them for
launches):

.. code-block:: yaml

    actions:
      ping-on-prem-host:
        type: codebuild
        project_name: ping-on-prem-host
        account_id: '0123456789010'
        region: 'eu-west-1'
        parameters:
          HOST_TO_PING:
            ssm:
              name: HOST_TO_PING
              region: eu-west-1


Note, these parameters can only be set in the action and can be overridden in the pre/post actions.  You cannot set these
globally nor can you set them at account level.  Here is an example of overriding a parameter:

.. code-block:: yaml

    launches:
      cloudtrail-spoke-enablement:
        portfolio: ccoe-security
        product: cloudtrail-spoke-enablement
        version: v1
        pre_actions:
          - name: check-cloudtrail-enabled
            parameters:
              HOST_TO_PING:
                ssm:
                  name: HOST_TO_PING
                  region: eu-west-1
        deploy_to:
          tags:
            - regions: default_region
              tag: type:spoke

.. note::

    actions were added in version 0.53.0

.. note::

    CodeBuild actions were added in version 0.53.0

When can I use actions?
-----------------------

pre_actions for launches
~~~~~~~~~~~~~~~~~~~~~~~~

The action is run before the product is provisioned. If the action fails the product is not provisioned and any
provisioning that depends on the provisioning will not be run.

To set up the action you must add it to the launch:

.. code-block:: yaml

    launches:
      cloudtrail-spoke-enablement:
        portfolio: ccoe-security
        product: cloudtrail-spoke-enablement
        version: v1
        pre_actions:
          - name: check-cloudtrail-enabled
        deploy_to:
          tags:
            - regions: default_region
              tag: type:spoke

You can use the pre_actions to verify conditions before a product is provisioned.

.. note::

    pre_actions for launches was added in version 0.53.0


post_actions for launches
~~~~~~~~~~~~~~~~~~~~~~~~~

The action is after the product is provisioned. If the action fails any provisioning that depends on the provisioning
will not be run.  The product that was provisioned correctly will not be rolled back due to the action failing.

To set up the action you must add it to the launch:

.. code-block:: yaml

    launches:
      vpc-for-spokes:
        portfolio: ccoe-networking
        product: vpc
        version: v1
        deploy_to:
          tags:
            - regions: default_region
              tag: type:spoke
        post_actions:
          - name: ping-on-prem-host

You can use the post_actions to verify the effect of a product provisioning.  For example, if you have provisioned a vpc
that gives you on-prem connectivity you can verify the connectivity works within your action - by pinging a host. Should
the action fail, the products that depend on the vpc product will not be launched.

.. note::

    post_actions for launches was added in version 0.53.0


pre_actions for spoke-local-portfolios
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The action is run before the portfolio is shared with an account. If the action fails the portfolio is not shared.

To set up the action you must add it to the spoke-local-portfolio:

.. code-block:: yaml

    spoke-local-portfolios:
      simple-example:
        portfolio: example-simple-central-it-team-portfolio
        pre_actions:
          - name: ensure-all-pipelines-are-green
        depends_on:
          - account-iam-for-spokes
        associations:
          - arn:aws:iam::${AWS::AccountId}:role/Admin
        constraints:
          launch:
            - product: account-vending-account-creation-shared
              roles:
                - arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole
        deploy_to:
          tags:
            - regions: enabled
              tag: type:spoke


post_actions for spoke-local-portfolios
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The action is run after the portfolio is shared with an account. If the action fails the portfolio remains shared.

To set up the action you must add it to the spoke-local-portfolio:

.. code-block:: yaml

    spoke-local-portfolios:
      simple-example:
        portfolio: example-simple-central-it-team-portfolio
        depends_on:
          - account-iam-for-spokes
        associations:
          - arn:aws:iam::${AWS::AccountId}:role/Admin
        constraints:
          launch:
            - product: account-vending-account-creation-shared
              roles:
                - arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole
        post_actions:
          - name: ensure-all-pipelines-are-green
        deploy_to:
          tags:
            - regions: enabled
              tag: type:spoke



You can use the pre_actions to verify conditions before a product is provisioned.

.. note::

    pre_actions for launches was added in version 0.53.0

What can I do with actions?
---------------------------

Canary releases
~~~~~~~~~~~~~~~
To run a canary test for a product you should start by having two launches.  The first launch would provision the given
product into an account and have a post_action to verify the product achieves the goal it was intended for.  The second
launch would depend on the first and provision the given product into a group of accounts (you can exclude the account
the first product was provisioned into using :ref:`exclude <How can I exclude an account or a sub Organizational unit from an expand>`).
The second product only provisions if the first does and if the post_action completes successfully.

Here is an example of what your manifest file may look like using a canary:

.. code-block:: yaml

    schema: puppet-2019-04-01

    accounts:
      - account_id: &canary_account_id '0123456789010'
        name: 'all-canary'
        default_region: &canary_default_region 'eu-west-1'
        regions_enabled:
          - eu-west-1
          - eu-west-2
        tags:
          - type:spoke
          - partition:eu
          - scope:pci
          - group:all-canary
      - ou: '/'
        name: 'all'
        default_region: eu-west-1
        regions_enabled:
          - eu-west-1
          - eu-west-2
        tags:
          - type:spoke
          - partition:eu
          - scope:pci
          - group:all
        exclude:
          accounts:
            - *canary_account_id

    launches:
      vpc-for-all-canary:
        portfolio: ccoe-networking
        product: vpc
        version: v1
        deploy_to:
          tags:
            - regions: default_region
              tag: group:all-canary
        post_actions:
          - name: ping-on-prem-host
      vpc-for-all:
        portfolio: ccoe-networking
        product: vpc
        version: v1
        depends_on:
          - vpc-for-all-canary
        deploy_to:
          tags:
            - regions: default_region
              tag: group:all

    actions:
      ping-on-prem-host:
        type: codebuild
        project_name: ping-on-prem-host
        account_id: *canary_account_id
        region: *canary_default_region
        parameters:
          HOST_TO_PING:
            ssm:
              name: HOST_TO_PING
              region: eu-west-1
