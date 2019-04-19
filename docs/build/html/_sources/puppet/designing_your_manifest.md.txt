Designing your manifest
=======================

## Purpose of the manifest file
The manifest file is there to describe what you want to provision and into which accounts you want to provision products
into.  It is possible to use AWS Organizations to make your manifest file more concise and easier to work with but the
premise is the same - it is just a list of accounts and AWS Service Catalog products.


## Sections of the manifest file
There are three sections to a manifest file - the global parameters, the accounts list and the launches.  Each of the 
three are described in the following sections.

### Parameters

It is possible to specify global parameters that should be used when provisioning your AWS Service Catalog Products.
You can set the value to an explicit value or you can set the value to the result of a function call - using funcation 
calls to set parameter values is known as using a macro.

Here is an example of a simple parameter:
```yaml
schema: puppet-2019-04-01

parameters:
    CloudTrailLoggingBucketName:
      default: cloudtrail-logs-for-aws
```
Whenever Puppet provisions a product it checks the parameters for the product.  If it sees the name match one of the 
parameter values it will use it.  In order to avoid clashes with parameter names we recommend using descriptive names 
like in the example - using the parameter names like ```BucketName``` will lead you into trouble pretty quickly.  

#### Macros 
You can also use a macro to set the value of a parameter.  It works in the same way as a normal parameter except it 
executes a function to get the value first.  Here is an an example:
```yaml
schema: puppet-2019-04-01

parameters:
    AllAccountIds:
      macro: 
        method: get_accounts_for_path
        args: /
```

At the moment there are the following macros supported:

```eval_rst
+------------------------+------------------------------+----------------------------------------------+ 
| macro method name      | args                         | description                                  |
+========================+==============================+==============================================+ 
| get_accounts_for_path  | ou path to get accounts for  | Returns a comma seperated list of account ids|
+------------------------+------------------------------+----------------------------------------------+
```

### Accounts
Description coming soon

### Launches
Description coming soon

### Example
```yaml
schema: puppet-2019-04-01

accounts:
  - account_id: '<YOUR_ACCOUNT_ID>'
    name: '<YOUR_ACCOUNT_NAME>'
    default_region: us-east-1
    regions_enabled:
      - us-east-1
      - us-west-2
    tags:
      - type:prod
      - partition:us
      - scope:pci

launches:
  account-iam-for-prod:
    portfolio: example-simple-central-it-team-portfolio
    product: account-iam
    version: v1
    parameters:
      RoleName:
        default: DevAdmin
      Path:
        default: /human-roles/
    deploy_to:
      tags:
        - tag: type:prod
          regions: default_region
```