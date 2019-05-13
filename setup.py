# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


with open("servicecatalog_puppet/requirements.txt", "r") as fh:
    requirements = fh.read().split("\n")

setuptools.setup(
    name="aws-service-catalog-puppet",
    version="0.0.42",
    author="Eamonn Faherty",
    author_email="aws-service-catalog-tools@amazon.com",
    description="Making it easier to deploy ServiceCatalog products",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/awslabs/aws-service-catalog-puppet-framework",
    packages=setuptools.find_packages(),
    package_data={'servicecatalog_puppet': ['*','*/*','*/*/*']},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    entry_points={
        'console_scripts': [
            'servicecatalog-puppet = servicecatalog_puppet.cli:cli'
        ]},
    install_requires=requirements,
)
