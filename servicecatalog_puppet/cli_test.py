#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import unittest
from unittest import mock

import yaml
from click.testing import CliRunner


class CLITest(unittest.TestCase):
    def setUp(self) -> None:
        from servicecatalog_puppet import cli

        self.sut = cli

    def test_deploy(self):
        # setup
        runner = CliRunner()
        mmm = mock.MagicMock()
        self.sut.core = mmm
        puppet_account_id = "01234567890"
        executor_account_id = "01234567890"

        # exercise
        with mock.patch.object(self.sut, "deploy_commands") as core_mocked:
            with mock.patch.object(self.sut, "config") as config_mocked:
                config_mocked.get_puppet_account_id.return_value = puppet_account_id
                config_mocked.get_current_account_id.return_value = executor_account_id
                config_mocked.get_should_explode_manifest.return_value = False
                with runner.isolated_filesystem():
                    with open("f.yaml", "w") as f:
                        f.write(yaml.safe_dump(dict()))

                        result = runner.invoke(
                            self.sut.cli, ["--info", "deploy", "f.yaml"]
                        )

                        # verify
                        print(result.exception)
                        self.assertEqual(result.exit_code, 0)
                        core_mocked.deploy.assert_called_once()
                        mocked_call = core_mocked.deploy.mock_calls[0]
                        ignorable, args, kwargs = mocked_call
                        self.assertEqual(args[1], puppet_account_id)
                        self.assertEqual(args[2], executor_account_id)
                        self.assertEqual(
                            kwargs,
                            dict(
                                execution_mode="hub",
                                single_account=None,
                                num_workers=10,
                                output_cache_starting_point="",
                                on_complete_url=None,
                            ),
                        )
