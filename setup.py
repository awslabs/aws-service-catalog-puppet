# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['servicecatalog_puppet', 'servicecatalog_puppet.workflow']

package_data = \
{'': ['*'],
 'servicecatalog_puppet': ['data/account-vending/*',
                           'data/manifest_utils/*',
                           'data/manifest_utils/accounts/*',
                           'data/manifest_utils/tags/*',
                           'data/manifest_utils_for_spoke_local_portfolios/*',
                           'manifests/*',
                           'templates/*']}

install_requires = \
['Click==7.0',
 'Jinja2==2.10.1',
 'MarkupSafe==1.1.1',
 'PyYAML==5.1',
 'better-boto==0.28.0',
 'boto3==1.14.22',
 'botocore==1.17.22',
 'certifi==2020.6.20',
 'cfn-flip==1.2.3',
 'chardet==3.0.4',
 'click==7.0',
 'colorclass==2.2.0',
 'docopt==0.6.2',
 'docutils==0.15.2',
 'idna==2.8',
 'jinja2==2.10.1',
 'jmespath==0.10.0',
 'lockfile==0.12.2',
 'luigi==2.8.9',
 'progressbar==2.5',
 'psutil==5.7.0',
 'pykwalify==1.7.0',
 'python-daemon==2.1.2',
 'python-dateutil==2.8.1',
 'pyyaml==5.1',
 'requests==2.22.0',
 's3transfer==0.3.3',
 'six==1.15.0',
 'terminaltables==3.1.0',
 'tornado==5.1.1',
 'urllib3>=1.25.9,<2.0.0']

entry_points = \
{'console_scripts': ['servicecatalog-puppet = servicecatalog_puppet.cli:cli']}

setup_kwargs = {
    'name': 'aws-service-catalog-puppet',
    'version': '0.76.8',
    'description': 'Making it easier to deploy ServiceCatalog products',
    'long_description': '# aws-service-catalog-puppet\n\n![logo](./docs/logo.png) \n\n## What is it?\nThis is a python3 framework that makes it easier to share multi region AWS Service Catalog portfolios and makes it \npossible to provision products into accounts declaratively using a metadata based rules engine.\n\nWith this framework you define your accounts in a YAML file.  You give each account a set of tags, a default region and \na set of enabled regions.\n\nOnce you have done this you can define portfolios should be shared with each set of accounts using the tags and you \ncan specify which regions the shares occur in.\n\nIn addition to this, you can also define products that should be provisioned into accounts using the same tag based \napproach.  The framework will assume role into the target account and provision the product on your behalf.\n\n\n## Getting started\n\nYou can read the [installation how to](https://service-catalog-tools-workshop.com/30-how-tos/10-installation/30-service-catalog-puppet.html)\nor you can read through the [every day use](https://service-catalog-tools-workshop.com/30-how-tos/50-every-day-use.html)\nguides.\n\nYou can read the [documentation](https://aws-service-catalog-puppet.readthedocs.io/en/latest/) to understand the inner \nworkings. \n\n\n## Going further\n\nThe framework is one of a pair.  The other is [aws-service-catalog-factory](https://github.com/awslabs/aws-service-catalog-factory).\nWith Service Catalog Factory you can create pipelines that deploy multi region portfolios very easily. \n\n## License\n\nThis library is licensed under the Apache 2.0 License. \n \n',
    'author': 'Eamonn Faherty',
    'author_email': 'aws-service-catalog-tools@amazon.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/awslabs/aws-service-catalog-puppet-framework',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
