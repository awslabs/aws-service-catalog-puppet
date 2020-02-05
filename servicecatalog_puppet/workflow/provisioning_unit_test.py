# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from pytest import fixture


@fixture
def module():
    from . import provisioning
    return provisioning


@fixture
def launch_name():
    return 'launch_name'


@fixture
def portfolio():
    return 'portfolio'


@fixture
def product():
    return 'product'


@fixture
def version():
    return 'version'


@fixture
def account_id():
    return 'account_id'


@fixture
def region():
    return 'region'


@fixture
def puppet_account_id():
    return 'puppet_account_id'


@fixture
def minimal_params(launch_name, portfolio, product, version, account_id, region, puppet_account_id):
    return {
        'launch_name': launch_name,
        'portfolio': portfolio,
        'product': product,
        'version': version,
        'account_id': account_id,
        'region': region,
        'puppet_account_id': puppet_account_id,
    }


@fixture
def dependencies():
    return [
        {
            'launch_name': 'launch_2',
            'portfolio': 'portfolio_2',
            'product': 'product_2',
            'version': 'version_2',
            'account_id': 'account_id_2',
            'region': 'region_2',
            'puppet_account_id': 'puppet_account_id_2',
        }
    ]


class TestProvisionProductTask():
    def test_priority(self, module, minimal_params):
        # setup
        expected_result = 3
        sut = module.ProvisionProductTask(**minimal_params, requested_priority=expected_result)

        # exercise
        actual_result = sut.priority

        # verify
        assert expected_result == actual_result

    #TODO - FIXME
    def aaaa_test_requires_generated_dependencies_happy_path(
        self, module, minimal_params, dependencies
    ):
        # setup
        expected_dependencies = dependencies
        sut = module.ProvisionProductTask(**minimal_params, dependencies=expected_dependencies)

        # exercise
        actual_result = sut.requires()

        # verify
        assert len(expected_dependencies) == len(actual_result.get('dependencies'))
        assert isinstance(actual_result.get('dependencies')[0], module.ProvisionProductTask)
        assert expected_dependencies[0] == actual_result.get('dependencies')[0].to_str_params(only_significant=True)

    def test_requires_generated_ssm_params_happy_path(
            self, module, minimal_params, mocker
    ):
        # setup
        mocker.patch.object(module, 'config')
        expected_ssm_params = {
            'Foo': {
            }
        }
        manifest_parameters = {
            'Foo': {
                'ssm': {
                    'name': 'bar',
                    'region': 'us-east-1',
                }
            }
        }
        sut = module.ProvisionProductTask(**minimal_params, manifest_parameters=manifest_parameters)

        # exercise
        actual_result = sut.requires()

        # verify
        assert len(expected_ssm_params.keys()) == len(actual_result.get('ssm_params').keys())
        get_ssm_param_task = actual_result.get('ssm_params').get('Foo')
        assert get_ssm_param_task.parameter_name == 'Foo'
        assert get_ssm_param_task.region == 'us-east-1'
        assert get_ssm_param_task.name == 'bar'

    def test_requires_generated_get_version_and_product_tasks(
            self, module, minimal_params, mocker,
            portfolio, product, version, account_id, region
    ):
        # setup
        mocker.patch.object(module, 'config')
        sut = module.ProvisionProductTask(**minimal_params)

        # exercise
        actual_result = sut.requires()

        # verify
        version_task = actual_result.get('version')
        assert version_task.to_str_params(only_significant=True) == {
            'portfolio': portfolio,
            'product': product,
            'version': version,
            'account_id': account_id,
            'region': region,
        }
        product_task = actual_result.get('product')
        assert product_task.to_str_params(only_significant=True) == {
            'portfolio': portfolio,
            'product': product,
            'account_id': account_id,
            'region': region,
        }
        provisioning_artifact_parameters_task = actual_result.get('provisioning_artifact_parameters')
        assert provisioning_artifact_parameters_task.to_str_params(only_significant=True) == {
            'portfolio': portfolio,
            'product': product,
            'version': version,
            'account_id': account_id,
            'region': region,
        }

    def test_params_for_results_display(
            self, module, minimal_params, mocker,
            launch_name, portfolio, product, version, account_id, region
    ):
        # setup
        sut = module.ProvisionProductTask(**minimal_params)

        # exercise
        actual_result = sut.params_for_results_display()

        # verify
        assert actual_result == {
            'launch_name': launch_name,
            'account_id': account_id,
            'region': region,
            'portfolio': portfolio,
            'product': product,
            'version': version,
        }
