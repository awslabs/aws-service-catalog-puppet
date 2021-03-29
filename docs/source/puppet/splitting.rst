Splitting up the workflow
=========================

How does ServiceCatalogPuppetWork
---------------------------------

Service Catalog Puppet converts your manifest file into a set of tasks that are subsequently run in a workflow that is
managed by Luigi.

When you use depends_on within your manifest file you are declaring that a set of tasks now depend on another set.  This
is creating sub workflows.

By default, every time Service Catalog Puppet runs it will try to execute each of the tasks in each of the sub workflows,
it does not even see any of the sub workflows, it just schedules the tasks as if there is one workflow.


What problems can this cause?
-----------------------------

By design, the Service Catalog Tools are developed to start simple and only increase in complexity when needed.

When the number of launches, spoke-local-portfolios, lambda executions, actions, regions or accounts grow to certain
size you may find that you want to optimise the workflow to speed it up.  You can do so by using AWS Orgs sharing,
task level caching or by optimising the way you build your AWS Service Catalog products or populate their parameters.

Eventually, you will most likely want to split your single pipeline run into smaller runs and only run pipelines
handling changes that needed instead of verifying all changes are still in place.


How can I fix this?
-------------------

Since version 0.99.0 there has been a second source for the servicecatalog-puppet-pipeline named ParameterisedSource.
This is an AWS S3 bucket which you can place a parameter file in.  When you place the parameter file in the bucket it
will trigger the pipeline.  The pipeline will use the latest version of your ServiceCatalogPuppet git repo for your
manifest file and will use the parameters you placed in the file to trigger a special run of the pipeline.

The options you specify must be placed in a parameters.yaml file, in a parameters.zip file in the root of your
parameters bucket.

Using the parameters file you can fine tune the pipeline to run a subset of the workflow by specifying one or more of
the following options:


Running the pipeline for a single account
#########################################

.. note::

    This was added in version 0.99.0

You can use the following attribute

.. code:: yaml

    single_account: ${SINGLE_ACCOUNT_ID}


Running the pipeline for a subset of operations
###############################################

.. note::

    This was added in version 0.101.0

You can use the following attribute:

.. code:: yaml

    subset:
      name: "remove-default-vpc-function"
      section: "launches"
      include_dependencies: true
      include_reverse_dependencies: true

name and section correspond to which operation you want to run in your pipeline.  Here we are saying run the launch
named remove-default-vpc-function.

include_dependencies is optional and defaults to false.  When set to false it does nothing.  When set to true if will
ensure that anything remove-default-vpc-function depends_on is included also.

include_reverse_dependencies is optional and defaults to false.  When set to false it does nothing.  When set to true if
will  ensure that anything depending on remove-default-vpc-function is included also.


Recommended use
###############

It is recommended you use this only if you are unable to operate with the full pipeline run.  When using this you are
managing the state yourself and it is easy to miss operations.  If you are using this we recommend running a regular
nightly or suitable other time based run to ensure you do not miss operations, regions or accounts.

When using this we recommend you turn off polling for source changes on your ServiceCatalogPuppet repo - this can be
done via the bootstrap command.  If you decide to stop using this you can turn on polling again and you back to how
you started.
