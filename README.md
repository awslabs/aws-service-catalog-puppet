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
pip install aws-service-catalog-puppet==0.0.8
```

### Bootstrap your account
Set up your spoke accounts:
```bash
servicecatalog-puppet bootstrap-spoke 0.0.8 <MASTER_ACCOUNT_ID>
```

### Bootstrap your account
Create the AWS CodeCommit repo and AWS CodePipeline resources to run the puppet for your 
master account:
```bash
servicecatalog-puppet bootstrap 0.0.8
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
