# aws-service-catalog-puppet

![logo](./docs/logo.png) 

## Badges

[![codecov](https://codecov.io/gh/awslabs/aws-service-catalog-puppet/branch/master/graph/badge.svg?token=e8M7mdsmy0)](https://codecov.io/gh/awslabs/aws-service-catalog-puppet)


## What is it?
This is a python3 framework that makes it easier to share multi region AWS Service Catalog portfolios and makes it 
possible to provision products into accounts declaratively using a metadata based rules engine.

With this framework you define your accounts in a YAML file.  You give each account a set of tags, a default region and 
a set of enabled regions.

Once you have done this you can define portfolios should be shared with each set of accounts using the tags and you 
can specify which regions the shares occur in.

In addition to this, you can also define products that should be provisioned into accounts using the same tag based 
approach.  The framework will assume role into the target account and provision the product on your behalf.


## Getting started

You can read the [installation how to](https://service-catalog-tools-workshop.com/30-how-tos/10-installation/30-service-catalog-puppet.html)
or you can read through the [every day use](https://service-catalog-tools-workshop.com/30-how-tos/50-every-day-use.html)
guides.

You can read the [documentation](https://aws-service-catalog-puppet.readthedocs.io/en/latest/) to understand the inner 
workings. 


## Going further

The framework is one of a pair.  The other is [aws-service-catalog-factory](https://github.com/awslabs/aws-service-catalog-factory).
With Service Catalog Factory you can create pipelines that deploy multi region portfolios very easily. 

## License

This library is licensed under the Apache 2.0 License. 
 
