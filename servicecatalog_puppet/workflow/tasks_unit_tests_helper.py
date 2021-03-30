import unittest
from unittest.mock import MagicMock


def mocked_client():
    context_handler_mock = MagicMock()
    client_mock = MagicMock()
    context_handler_mock.return_value.__enter__.return_value = client_mock
    return client_mock, context_handler_mock


class PuppetTaskUnitTest(unittest.TestCase):
    def wire_up_mocks(self):
        self.spoke_client_mock, self.sut.spoke_client = mocked_client()
        (
            self.spoke_regional_client_mock,
            self.sut.spoke_regional_client,
        ) = mocked_client()

        self.hub_client_mock, self.sut.hub_client = mocked_client()
        self.hub_regional_client_mock, self.sut.hub_regional_client = mocked_client()

        self.sut.write_output = MagicMock()
        self.sut.input = MagicMock()

    def assert_spoke_regional_client_called_with(
        self, client_used, function_name_called, function_parameters
    ):
        self.sut.spoke_regional_client.assert_called_once_with(client_used)

        function_called = getattr(self.spoke_regional_client_mock, function_name_called)
        function_called.assert_called_once_with(**function_parameters)

    def assert_output(self, expected_output):
        self.sut.write_output.assert_called_once_with(expected_output)
