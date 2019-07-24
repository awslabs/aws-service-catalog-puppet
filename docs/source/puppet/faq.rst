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
