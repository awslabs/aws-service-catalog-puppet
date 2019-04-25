Notifications
=============

You can listen to the AWS CloudFormation stack events from your product provisioning.

This is the recommended way of discovering provisioning errors.

When you bootstraped your account you will have created an AWS SNS Topic: 
```servicecatalog-puppet-cloudformation-events``` in your default region.

Please note this will only receive notifications for products provisioned using 
ServiceCatalog-Puppet - any self service vending from AWS Service Catalog will not 
use this topic.