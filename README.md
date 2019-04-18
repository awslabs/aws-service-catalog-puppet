## AWS Service Catalog Puppet Framework

![logo](./docs/logo.png) 

This is a framework where you list your AWS accounts with tags and your AWS Service Catalog products with tags or target
accounts. The framework works through your lists, dedupes and spots collisions and then provisions the products into your 
AWS accounts for you. It handles the Portfolio sharing, its acceptance and can provision products cross account and cross 
region.

### High level architecture diagram

![whatisthis](./docs/whatisthis.png)

This is a framework where you list your AWS accounts with tags and your AWS Service Catalog products with tags or 
target accounts.  The framework works through your lists, dedupes and spots collisions and then provisions the products
into your AWS accounts for you.  It handles the Portfolio sharing, its acceptance and can provision products cross account
and cross region.

## Getting started

Follow the steps below to get started:

### Install the tool
Optional, but recommended:
```bash
virtualenv --python=python3.7 venv
source venv/bin/activate
```

Install the package:
```bash
pip install aws-service-catalog-puppet
```

### Bootstrap your account
Set up your spoke accounts:
```bash
servicecatalog-puppet bootstrap-spoke <MASTER_ACCOUNT_ID>
```

### Bootstrap your account

There are two parts to bootstrapping the puppet.  The first is concerned with setting the global configurations.  To do 
this we use AWS SSM Parameters.  To get setup you need to create a configuration file with a list of regions you want to 
use - for example config.yaml:

```yaml
regions: [
  'us-east-2',
  'us-east-1',
  'us-west-1',
  'us-west-2',
  'ap-south-1',
  'ap-northeast-2',
  'ap-southeast-1',
  'ap-southeast-2',
  'ap-northeast-1',
  'ca-central-1',
  'eu-central-1',
  'eu-west-1',
  'eu-west-2',
  'eu-west-3',
  'sa-east-1',
]
```
Once you have this file you need to upload the config:
```bash
servicecatalog-puppet upload-config config.yaml
```

If you make changes to this you will need to run upload-config and bootstrap commands again for the changes to occur.

Once that has completed you are ready to bring up the rest of the puppet.

Create the AWS CodeCommit repo and AWS CodePipeline resources to run the puppet for your 
master account:
```bash
servicecatalog-puppet bootstrap
```

### Setup your puppet
Clone the configuration repo and configure your factory:
```bash
git clone --config 'credential.helper=!aws codecommit credential-helper $@' --config 'credential.UseHttpPath=true' https://git-codecommit.eu-west-1.amazonaws.com/v1/repos/ServiceCatalogPuppet
servicecatalog-puppet seed simple ServiceCatalogPuppet
cd ServiceCatalogPuppet
git add .
git commit -am "initial add"
git push
```
Wait for pipeline to complete and you have a working puppet.

## License

This library is licensed under the Apache 2.0 License. 
