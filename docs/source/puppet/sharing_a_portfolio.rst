Sharing a portfolio
===================

-------------------------------------
What is sharing and how does it work?
-------------------------------------

.. note::

    This was added in version 0.1.14

This framework allows you to create portfolios in other accounts that mirror the portfolio in your hub account.  The
framework will create the portfolio for you and copy the products (along with their versions) from your hub account into
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
