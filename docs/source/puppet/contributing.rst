Contributing
============

General Advice
--------------

If you are planning on building a feature please raise a github issue describing the requirement to ensure someone else
is not already building the same capability.

When you raise the github issue please explain how you are going to architect the capability.  There are some pointers
here on design principals but it would be good to get some visibility on what you are planning sooner rather than later.


Building locally
----------------

You can build and run this framework locally.  There is a Makefile to make this easier for you.  In order to run the
Make targets you will need to have python poetry and python 3.7 installed.  We recommend using pipx to install poetry.

The following describes some of the Make targets.

make black
----------
----------


Hub
---

Hub is the default.  It means all provisioning occurs in the main AWS CodeBuild project in the puppet account.  During a
hub execution the CodeBuild project will wait for each execution to complete before processing its dependents.


Async
-----

.. note::

    This was added in version 0.76.0

With async the provisioning still occurs in the CodeBuild project of the puppet account but when provisioning of
launches is running the CodeBuild project does not wait for the completion of the product provisioning.  This means you
cannot depend on a launch that is async and you cannot have outputs for an async launch.