# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pytest import fixture
import pkg_resources

@fixture
def sut():
    from servicecatalog_puppet import cli
    return cli


def test_bootstrap_stack_name(sut):
    assert sut.BOOTSTRAP_STACK_NAME == 'servicecatalog-puppet'


def test_service_catalog_factory_repo_name(sut):
    assert sut.SERVICE_CATALOG_PUPPET_REPO_NAME == 'ServiceCatalogPuppet'
