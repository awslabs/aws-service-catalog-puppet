import unittest


class PuppetTaskUnitTest(unittest.TestCase):

    def setUp(self) -> None:
        from servicecatalog_puppet.commands import task_reference

        self.module = task_reference
        self.sut = task_reference.generate_task_reference

    def test_something(self):
        self.assertEqual(True, False)