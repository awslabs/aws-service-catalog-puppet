Getting up and running
======================

ServiceCatalog-Puppet runs in your AWS Account.  In order for you to install it into your account you can use the 
aws-service-catalog-puppet cli.  This is distributed via [PyPi](https://pypi.org/project/aws-service-catalog-puppet/)


What am I going to install?
---------------------------

Once you have completed the install you will have the following pipeline in your account:


.. image:: ./puppet-getting-started-what-am-i-going-to-install-pipeline.png


using the following services:

.. image:: ./puppet-getting-started-what-am-i-going-to-install.png



Before you install
------------------

You should consider which account will be the home for your puppet.  This account will contain the AWS CodePipelines
and will need to be accessible to any accounts you would like to share with.  If you are using ServiceCatalog-Factory,
we recommend you install both tools into the same account. 
 

Installing
-------------------

see https://service-catalog-tools-workshop.com/installation.html
