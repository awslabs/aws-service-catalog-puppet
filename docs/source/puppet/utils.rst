Utils
=====

The following utils will help you manage your AWS Accounts when using ServiceCatalog-Puppet:


show-resources
--------------

.. note::

    This was added in version 0.7.0

You can use the ``servicecatalog-puppet`` cli to list all the resources that will be created to bootstrap the framework

.. code-block:: bash

    servicecatalog-puppet show-resources


Will return the following markdown:

.. code-block:: bash





    n.b. AWS::StackName evaluates to servicecatalog-puppet


run
---

.. note::

    This was added in version 0.3.0

The run command will run the main AWS CodePipeline ``servicecatalog-puppet-pipeline``

.. code-block:: bash

    servicecatalog-puppet run

You can also tail the command to watch the progress of the pipeline.  It is a little underwhelming at the moment.


.. code-block:: bash

    servicecatalog-puppet run --tail


list-launches
-------------

The list-launches command can currently only be invoked on an expanded manifest.yaml file.  To
expand your manifest you must run the following:


.. code-block:: bash

    servicecatalog-puppet expand manifest.yaml

This will create a file named ``manifest-expanded.yaml in the same directory``.

You can then run ``list-launches``:

.. code-block:: bash

    servicecatalog-puppet list-launches manifest-expanded.yaml
