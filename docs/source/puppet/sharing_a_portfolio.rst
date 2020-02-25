Sharing a portfolio
===================

-------------------------------------
What is sharing and how does it work?
-------------------------------------

.. note::

    This was added in version 0.1.14

This framework allows you to create portfolios in other accounts that mirror the portfolio in your hub account.  The
framework will create the portfolio for you and either copy or import the products (along with their versions) from your hub account into
the newly created portfolio.

In addition to this, you can specify associations for the created portfolio and add launch constraints for the products.


.. warning::

    Once a hub product version has been copied into a spoke portfolio it will not be updated.

--------------------
How can I set it up?
--------------------

The following is an example of how to add the portfolio ``example-simple-central-it-team-portfolio`` to all spokes tagged
``scope:spoke``:

.. code-block:: yaml

    spoke-local-portfolios:
      account-vending-for-spokes:
        portfolio: example-simple-central-it-team-portfolio
        depends_on:
          - account-iam-for-spokes
        associations:
          - arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole
        constraints:
          launch:
            - product: account-vending-account-creation-shared
              roles:
                - arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole
        products_copy_or_import: copy
        deploy_to:
          tags:
            - tag: scope:spoke
              regions: default_region

The example above will create the portfolio once the ``depends_on`` launches have completed successfully.

The valid values for regions are:
- enabled - this will deploy to each enabled region for the account
- regions_enabled - this will deploy to each enabled region for the account
- default_region - this will deploy to the default region specified for the account
- all - this will deploy to all regions enabled in your config (whilst setting up Puppet)
- list of AWS regions - you can type in a list of AWS regions (each region selected should be present in your config)


What is the setting for Products Copy or Import?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

    This was added in version 0.72.0, previous versions always Copy

Using ``spoke-local-portfolios``, a spoke portfolio is always created as a copy of the hub portfolio - that is, it has 
a different portfolio ID, but the same name and metadata as the hub portfolio. This ensures changes made to the 
portfolio in the spoke (such as associations and constraints) cannot affect other spokes or the hub portfolio.

There are 2 options for populating products inside the spoke portfolios, Copy or Import.

| ``products_copy_or_import: copy`` (the default) means that products and provisioning artifacts are deep-copied into 
  the spoke local portfolio using the Service Catalog ``CopyProduct`` API call. 
| They will get new product and provisioning artifact IDs, but have the same names and metadata as hub products.
| This ensures isolation between hub and spoke - changes to products and versions in the hub will only be 
  reflected in the spoke on the next puppet run.


| ``products_copy_or_import: import`` setting will import (using the ``AssociateProductWithPortfolio`` Service Catalog API call) the product and 
  its provisioning artifacts into the spoke from the hub portfolio with the same IDs as the hub portfolio.
| This is useful for occasions where is it necessary to have the same product ID in the spoke as in the hub - 
  for example if changes to provisioning artifacts in the hub need to be instantly reflected in the spoke 
  without requiring a puppet run.


How can I add an association?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The example above will add an association for the IAM principal:

``arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole``

so the portfolio will be accessible for anyone assuming that role.  In addition to roles, you can also specify the ARN of
users and groups.

.. note::

    Using ``${AWS::AccountId}`` will evaluate in the spoke account.


How can I add a launch constraint?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The example above will add a launch constraint for the IAM role:

``arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole``

so they can launch the product ``account-vending-account-creation-shared`` in the spoke account.

.. warning::

    You can only specify an IAM role and the role must be assumable by the AWS service principal ``servicecatalog.amazonaws.com``

.. note::

    Using ``${AWS::AccountId}`` will evaluate in the spoke account.


.. note::

    Support for using ``products`` was added in version 0.3.0.

You can use ``products`` instead of ``product`` to specify either a list of products or use a regular expression. The
regular expression is matched using Python3 ``re.match``.

Using a list:

.. code-block:: yaml

    spoke-local-portfolios:
      account-vending-for-spokes:
        portfolio: example-simple-central-it-team-portfolio
        depends_on:
          - account-iam-for-spokes
        associations:
          - arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole
        constraints:
          launch:
            - products:
                - account-vending-account-bootstrap-shared
                - account-vending-account-creation-shared
              roles:
                - arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole
        deploy_to:
          tags:
            - tag: scope:spoke
              regions: default_region


Using a regular expression:

.. code-block:: yaml

    spoke-local-portfolios:
      account-vending-for-spokes:
        portfolio: example-simple-central-it-team-portfolio
        depends_on:
          - account-iam-for-spokes
        associations:
          - arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole
        constraints:
          launch:
            - products: "account-vending-account-*"
              roles:
                - arn:aws:iam::${AWS::AccountId}:role/MyServiceCatalogAdminRole
        deploy_to:
          tags:
            - tag: scope:spoke
              regions: default_region


-----------------------------------------------
What is the recommended implementation pattern?
-----------------------------------------------

#. Add an entry to launches that will provision a product into to your matching spokes.  This product should provide the IAM roles your users will assume to interact with the portfolio you are going to add.

#. Add an entry to spoke-local-portfolios to add a portfolio to your matching spokes.  This should depend on the product you launched that contains the IAM roles you added to the launches section of your manifest.

-------------------------------------
Is there anything else I should know?
-------------------------------------
#. It would be good to become familar with the `AWS Service Catalog pricing <https://aws.amazon.com/servicecatalog/pricing/>`_ before using this feature.
