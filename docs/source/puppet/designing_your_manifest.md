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

With the accounts section, you can describe your AWS accounts.  You can set a default region, the enabled regions and 
you can tag your accounts.  This metadata describing your account is used to determine which packages get deployed into
your accounts.

#### Setting a default region
Within your account you may have a _home_ or a default region.  This may be the closest region to the team using the 
account.  You use ```default_region``` when describing your account and then you can use ```default_region``` again as a
target when you specify your product launches - the product will be provisioned into the region specified.

Here is an example with a ```default_region``` set to ```us-east-1```:

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
```

Please note ```default_region``` can only be a string.

#### Setting enabled regions
You may chose not to use every region within your AWS Account.  When describing an AWS account you can specify which 
regions are enabled for an account using ```regions_enabled```.

Here is an example with ```regions_enabled``` set to ```us-east-1 and us-west-2```:

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
```

Please note ```regions_enabled``` can only be a list of strings.


#### Setting tags
You can describe your account using tags.  Tags are specified using a list of strings.  We recommend using namespaces 
for your tags, adding an extra dimension to them.  If you choose to do this you can use a colon to split name and values.

Here is an example with namespaced tags:
   
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
```

In this example there the following tags:
- namespace of type and value of prod
- namespace of partition and value of us
- namespace of scope and value of pci.

The goal of tags is to provide a classification for your accounts that can be used to a deployment time.  

#### Using an OU id or path (integration with AWS Organizations)
When specifying an account you can use short hand notation of ```ou``` instead of ```account_id``` to build out a list 
of accounts with the same properties.

For example you can use an AWS Organizations path:
```yaml
schema: puppet-2019-04-01

accounts:
  - ou: /prod
    name: '<YOUR_ACCOUNT_NAME>'
    default_region: us-east-1
    regions_enabled:
      - us-east-1
      - us-west-2
    tags:
      - type:prod
      - partition:us
      - scope:pci
```

The framework will get a list of all AWS accounts within the ```/prod``` Organizational unit and expand your manifest to
look like the following  (assuming accounts 0123456789010 and 0109876543210 are the only accountss within ```/prod```):

```yaml
schema: puppet-2019-04-01

accounts:
  - account_id: 0123456789010
    name: '<YOUR_ACCOUNT_NAME>'
    default_region: us-east-1
    regions_enabled:
      - us-east-1
      - us-west-2
    tags:
      - type:prod
      - partition:us
      - scope:pci
  - account_id: 0109876543210
    name: '<YOUR_ACCOUNT_NAME>'
    default_region: us-east-1
    regions_enabled:
      - us-east-1
      - us-west-2
    tags:
      - type:prod
      - partition:us
      - scope:pci
```

### Launches
Launches allow you to decide which products get provisioned into each account.  You link product launches to accounts 
using tags or explicit account ids and you can set which regions the products are launched into.

#### Tag based launches
You can specify a launch to occur using ```tags``` in the ```deploy_to``` section of a launch.  

Here is an example, it deploys a ```v1``` of a product named ```account-iam``` from the portfolio 
```example-simple-central-it-team-portfolio``` into into the ```default_region``` of all accounts tagged ```type:prod```:  

```yaml
schema: puppet-2019-04-01

launches:
  account-iam-for-prod:
    portfolio: example-simple-central-it-team-portfolio
    product: account-iam
    version: v1
    deploy_to:
      tags:
        - tag: type:prod
          regions: default_region
```


#### Account based launches
You can also specify a launch to occur explicity in an account by using the ```accounts``` section in the 
```deploy_to``` section of a launch.  

Here is an example, it deploys a ```v1``` of a product named ```account-iam``` from the portfolio 
```example-simple-central-it-team-portfolio``` into into the ```default_region``` of the accounts ```0123456789010```:  

```yaml
schema: puppet-2019-04-01

launches:
  account-iam-for-prod:
    portfolio: example-simple-central-it-team-portfolio
    product: account-iam
    version: v1
    deploy_to:
      accounts:
        - account_id: '0123456789010'
          regions: default_region
```