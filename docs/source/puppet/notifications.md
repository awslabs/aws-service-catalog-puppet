Notifications
=============

You can listen to the AWS CloudFormation stack events from your product provisioning.

This is the recommended way of discovering provisioning errors.

When you bootstraped your account you will have created an AWS SQS Queue: 
```servicecatalog-puppet-cloudformation-events``` in your default region.

You will also have SNS Topics in each region configured to push events to this queue:
```servicecatalog-puppet-cloudformation-regional-events```

Please note this will only receive notifications for products provisioned using 
ServiceCatalog-Puppet - any self service vending from AWS Service Catalog will not 
publish to this queue.

You should handle consuming the queue and have your own error handling code.