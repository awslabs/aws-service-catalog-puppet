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
        executor_account_id = puppet_account_id

        # exercise
        with mock.patch.object(self.sut, 'core') as core_mocked:
            with mock.patch.object(self.sut, 'config') as config_mocked:
                config_mocked.get_puppet_account_id.return_value = puppet_account_id
                with runner.isolated_filesystem():
                    with open('f.yaml', 'w') as f:
                        f.write(yaml.safe_dump(dict()))

                        result = runner.invoke(self.sut.cli, ['--info',  'deploy', 'f.yaml'])

                        # verify
                        self.assertEqual(result.exit_code, 0)
                        core_mocked.deploy.assert_called_once()
                        mocked_call = core_mocked.deploy.mock_calls[0]
                        ignorable, args, kwargs = mocked_call
                        self.assertEqual(args[1], puppet_account_id)
                        self.assertEqual(kwargs, dict(
                            execution_mode='hub',
                            single_account=None,
                            num_workers=10,
                            on_complete_url=None,
                        ))
