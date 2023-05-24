#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import unittest
from unittest import mock

SPOKE_REGIONAL_CLIENT = "SPOKE_REGIONAL_CLIENT"


def mocked_client():
    context_handler_mock = mock.MagicMock()
    client_mock = mock.MagicMock()
    context_handler_mock.return_value.__enter__.return_value = client_mock
    return client_mock, context_handler_mock


class Paginator:
    def __init__(self, items, expected_kwargs):
        self.items = items
        self.expected_kwargs = expected_kwargs

    def paginate(self, **kwargs):
        if self.expected_kwargs != kwargs:
            raise Exception(
                f"Expected paginate kwargs {self.expected_kwargs} but got {kwargs}"
            )
        return self.items


class Manager:
    def __init__(self):
        self.expected_requests_and_responses = []
        self.index = 0

    def add_expected_request_and_response(
        self,
        client_type,
        client_name,
        uses_paginator,
        request_name,
        request_parameters,
        response_to_return,
    ):
        self.expected_requests_and_responses.append(
            (
                client_type,
                client_name,
                uses_paginator,
                request_name,
                request_parameters,
                response_to_return,
            )
        )

    def get_attribute_for(
        self,
        actual_client_type,
        actual_service,
        actual_method,
        actual_region_name,
        actual_retry_max_attempts,
    ):
        (
            expected_client_type,
            expected_client_name,
            expected_uses_paginator,
            expected_method,
            expected_parameters,
            response_to_return,
        ) = self.expected_requests_and_responses[self.index]
        # self.index += 1

        if actual_client_type != actual_client_type:
            raise Exception(
                f"Expected client type {expected_client_type} but got {actual_client_type}"
            )

        if actual_service != expected_client_name:
            raise Exception(
                f"Expected client name {expected_client_name} but got {actual_service}"
            )

        if expected_uses_paginator:
            if actual_method != "get_paginator":
                raise Exception(
                    f"Expected a paginator to be requested but {actual_method} was requested instead"
                )

            def paginator_to_return(*args, **kwargs):
                if args[0] != expected_method:
                    raise Exception(
                        f"Expected paginator: {expected_method} does not match actual: {args[0]}"
                    )
                return Paginator(response_to_return, expected_parameters)

            return paginator_to_return

        else:
            if actual_method != expected_method:
                raise Exception(
                    f"Expected request name {expected_method} but got {actual_method}"
                )

            def call_to_return(*args, **kwargs):
                if kwargs != expected_parameters:
                    raise Exception(
                        f"Expected parameters: {expected_parameters} does not match actual: {kwargs}"
                    )
                return response_to_return

            return call_to_return


class FakeClientContextManager:
    def __init__(
        self, client_type, manager, service, region_name=None, retry_max_attempts=None
    ):
        self.client_type = client_type
        self.manager = manager
        self.service = service
        self.region_name = region_name
        self.retry_max_attempts = retry_max_attempts
        self.expected_requests_and_responses = []

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.expected_requests_and_responses = []

    def __getattr__(self, attr):
        if attr == "manager":
            return self.manager
        elif attr == "client_type":
            return self.client_type
        elif attr == "args":
            return self.args
        elif attr == "kwargs":
            return self.kwargs
        else:
            return self.manager.get_attribute_for(
                SPOKE_REGIONAL_CLIENT,
                self.service,
                attr,
                self.region_name,
                self.retry_max_attempts,
            )


class PuppetTaskUnitTest(unittest.TestCase):
    task_reference = "task_reference"
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"

    def get_common_args(self):
        return dict(
            task_reference="task_reference",
            manifest_task_reference_file_path="manifest_task_reference_file_path",
            manifest_files_path=self.manifest_file_path,
            dependencies_by_reference="dependencies_by_reference",
            puppet_account_id="puppet_account_id",
        )

    drift_token = "NOW"
    run_token = "NOW"

    def wire_up_mocks(self):
        self.sut.write_output = mock.MagicMock()
        self.sut.write_empty_output = mock.MagicMock()

        self.manager = Manager()

        # start of spoke_regional_client
        def fake_spoke_regional_client(
            service, region_name=None, retry_max_attempts=None
        ):
            return FakeClientContextManager(
                SPOKE_REGIONAL_CLIENT,
                self.manager,
                service,
                region_name,
                retry_max_attempts,
            )

        self.sut.spoke_regional_client = mock.MagicMock(
            side_effect=fake_spoke_regional_client
        )

    def add_expected_request_and_response(
        self,
        client_type,
        client_name,
        request_name,
        request_parameters,
        response_to_return,
    ):
        self.manager.add_expected_request_and_response(
            client_type,
            client_name,
            False,
            request_name,
            request_parameters,
            response_to_return,
        )

    def add_expected_paginated_request_and_response(
        self,
        client_type,
        client_name,
        request_name,
        request_parameters,
        response_to_return,
    ):
        self.manager.add_expected_request_and_response(
            client_type,
            client_name,
            True,
            request_name,
            request_parameters,
            response_to_return,
        )

    def assert_output(self, expected_output):
        self.sut.write_output.assert_called_once_with(expected_output)

    def assert_empty_output(self):
        self.sut.write_empty_output.assert_called_once()
