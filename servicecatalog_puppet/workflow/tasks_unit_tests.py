import unittest
import json


class PuppetTaskUnitTest(unittest.TestCase):
    expectations = None

    def setUp(self) -> None:
        self.expectations = list()

    def expect_call(self, mock, client_details, api_call, api_kwargs, return_value):
        f = mock.CrossAccountClientContextManager().__enter__()
        f.configure_mock(**{f"{api_call}.return_value": return_value})
        self.expectations.append((client_details, api_call, api_kwargs))

    def verify(self, mock):
        index = 0
        OFFSET = 2 * len(self.expectations)
        mock_calls = mock.CrossAccountClientContextManager.mock_calls
        for expected in self.expectations:
            ignored, client_args, client_kwargs = mock_calls[OFFSET + (index * 4)]
            kwargs, expected_api_call, expected_api_kwargs = expected
            expected_args = (
                kwargs.get("service"),
                kwargs.get("role"),
                kwargs.get("session"),
            )
            self.assertEqual(expected_args, client_args, "Client args were not found")
            for arg_name, arg_value in client_kwargs.items():
                self.assertEqual(kwargs.get(arg_name), arg_value, "kwargs do not match")
            api_call, api_args, api_kwargs = mock_calls[
                OFFSET + (index * 4) + 2
            ]  # TODO may break on multiples
            api_call = api_call.split(".")[-1]
            self.assertEqual(expected_api_call, api_call, "API call didn't match")
            self.assertEqual(expected_api_kwargs, api_kwargs, "API kwargs didn't match")
            index += 1

        self.assertEqual(
            OFFSET + (4 * len(self.expectations)),
            len(mock_calls),
            "fewer or too many API calls were made",
        )

    def verify_output(self, expected):
        actual = self.sut.output().open().read()
        self.assertEqual(json.dumps(expected, indent=4, default=str,), actual)
