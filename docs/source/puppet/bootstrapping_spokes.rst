Bootstrapping Spokes
====================

ServiceCatalog-Puppet runs in a hub and spoke model.  Your spokes must be bootstrapped so that they can work with the
puppet account.


You have some options when it comes to bootstrapping spokes.


Individual Spokes
-----------------

To bootstrap a spoke you can use the cli

Bootstrap your spoke
~~~~~~~~~~~~~~~~~~~~

You will need to bootstrap each of your spokes.  In order to do so please export your credentials and set your profile,
then run the following:

.. code-block:: bash

    servicecatalog-puppet bootstrap-spoke <ACCOUNT_ID_OF_YOUR_PUPPET>

Bootstrap your spoke as
~~~~~~~~~~~~~~~~~~~~~~~

If your current credentials are not for a role in the account you want to bootstrap but you can assume a role to get
there then you can use bootstrap-spoke-as:

.. code-block:: bash

    servicecatalog-puppet bootstrap-spoke-as <ACCOUNT_ID_OF_YOUR_PUPPET> <ARN_OF_IAM_ROLE_TO_ASSUME_BEFORE_BOOTSTRAPPING>


You can specify multiple ARNs and they will be assumed from left to right before bootstrapping:

.. code-block:: bash

    servicecatalog-puppet bootstrap-spoke-as <ACCOUNT_ID_OF_YOUR_PUPPET> <ARN_1> <ARN_2> <ARN_3> <ARN_4>

With the above example the framework will assume the role defined in ARN_1, then assume the role in ARN_2, then assume
the role in ARN_3 and finally then assume the role in ARN_4 before bootstrapping.


Groups of Spokes
----------------

You can bootstrap groups of accounts also.

Bootstrap all accounts in an OU via the cli
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should export credentials that allow you to list accounts in your org and allow you to assume a role in the spoke
accounts so they can be bootstrapped.  Once you have done this you can use:

.. code-block:: bash

    servicecatalog-puppet bootstrap-spokes-in-ou <OU_PATH_OR_ID> <NAME_OF_IAM_ROLE_TO_ASSUME_BEFORE_BOOTSTRAPPING>

The name of IAM role you specify should have the permission in the target ou accounts to bootstrap the spokes.  For
example, the following will assume the role DevOpsAdminRole in the spokes contained in the /dev ou in order to bootstrap:


.. code-block:: bash

    servicecatalog-puppet bootstrap-spokes-in-ou /dev DevOpsAdminRole

If your current role does not allow you to list accounts in the org or allow you to assume role cross account you can
specify an ARN of a role that does.  When you do so the framework will assume that role first and then perform the
bootstrapping.

.. code-block:: bash

    servicecatalog-puppet bootstrap-spokes-in-ou /dev DevOpsAdminRole arn:aws:iam::0123456789010:role/OrgUserRole

.. note::

    bootstrap-spokes-in-ou was added in version 0.44.0


Bootstrap all accounts in an OU via CodeBuild
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In your account you can find an AWS CodeBuild project named: `servicecatalog-puppet-bootstrap-an-ou`

You start a run of that project and override the environmental variables to use bootstrap-spokes-in-ou.

.. note::

    bootstrap-spokes-in-ou was added in version 0.44.0


Restricting Spokes
------------------

When you are bootstrapping a spoke you can specify the ARN of an IAM Permission Boundary that should be applied to the
spokes PuppetRole.  This permission boundary should permit the PuppetRole to interact with AWS Service Catalog to accept
shares, manage portfolios and to add, provision and terminate products.  In addition the role should allow the use of
AWS SNS, AWS EventBridge, AWS OpsCenter.

To use the boundary you must bootstrap a spoke using an extra parameter:

.. code-block:: shell

    servicecatalog-puppet bootstrap-spoke <ACCOUNT_ID_OF_YOUR_PUPPET> --permission-boundary arn:aws:iam::aws:policy/AdministratorAccess


The parameter is available on `bootstrap-spoke-as` and `bootstrap-spokes-in-ou` also.

.. note::

    permission boundary was added in version 0.56.0


Customising the PuppetRole
--------------------------

When you bootstrap a spoke you can specify an optional `puppet-role-name` and `puppet-role-path`:

.. code-block:: bash

    servicecatalog-puppet bootstrap-spoke <ACCOUNT_ID_OF_YOUR_PUPPET> --puppet-role-name PuppetExecutionRole --puppet-role-path /automation/

Please note you must choose the same PuppetRoleName and PuppetRolePath for each spoke in your environment and you must
choose that same PuppetRoleName and PuppetRolePath when bootstrapping the hub account:

.. code-block: bash

    servicecatalog-puppet bootstrap --puppet-role-name PuppetExecutionRole --puppet-role-path /automation/ ...

You can have two independent hub accounts and bootstrap a spoke twice so that it can be managed by two independent hub
accounts so long as the PuppetRoleName and PuppetRolePath are different.

.. note::

    configurable puppet role name and paths were added in version 0.91.0
