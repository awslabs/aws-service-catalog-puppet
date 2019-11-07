# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="aws-service-catalog-puppet",
    version="0.47.0",
    author="Eamonn Faherty",
    author_email="aws-service-catalog-tools@amazon.com",
    description="Making it easier to deploy ServiceCatalog products",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/awslabs/aws-service-catalog-puppet-framework",
    packages=find_packages(),
    package_data={"servicecatalog_puppet": ["*", "*/*", "*/*/*"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    entry_points={
        "console_scripts": ["servicecatalog-puppet = servicecatalog_puppet.cli:cli"]
    },
    install_requires=[
        "better-boto==0.20.1",
        "boto3==1.10.12",
        "botocore==1.13.12",
        "certifi==2019.9.11",
        "cfn-flip==1.2.1",
        "chardet==3.0.4",
        "click==7.0",
        "colorclass==2.2.0",
        "docopt==0.6.2",
        "docutils==0.14",
        "idna==2.8",
        "jinja2==2.10.1",
        "jmespath==0.9.4",
        "lockfile==0.12.2",
        "luigi==2.8.9",
        "markupsafe==1.1.1",
        "pykwalify==1.7.0",
        "python-daemon==2.1.2",
        "python-dateutil==2.8.0; python_version >= '2.7'",
        "pyyaml==5.1",
        "requests==2.22.0",
        "s3transfer==0.2.1",
        "six==1.13.0",
        "terminaltables==3.1.0",
        "tornado==5.1.1",
        "urllib3==1.25.6; python_version >= '3.4'",
    ],
)
