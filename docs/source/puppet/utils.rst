Utils
=====

The following utils will help you manage your AWS Accounts when using ServiceCatalog-Puppet:

run
===

.. note::

    This was added in version 0.3.0

The run command will run the main AWS CodePipeline ``servicecatalog-puppet-pipeline``

.. code-block:: bash

    servicecatalog-puppet run

You can also tail the command to watch the progress of the pipeline.  It is a little underwhelming at the moment.


.. code-block:: bash

    servicecatalog-puppet run --tail


list-launches
=============

The list-launches command can currently only be invoked on an expanded manifest.yaml file.  To
expand your manifest you must run the following:


.. code-block:: bash

    servicecatalog-puppet expand manifest.yaml

This will create a file named ``manifest-expanded.yaml in the same directory``.

You can then run ``list-launches``:

.. code-block:: bash

    servicecatalog-puppet list-launches manifest-expanded.yaml
