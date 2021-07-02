import os

import parso
import glob

from parso.python import tree

ignored = [
    "section_name",
    "get_klass_for_provisioning",
    "get_sharing_policies",
    "output_suffix",
    "get_all_params",
    "complete",
    "load_from_input",
    "generate_new_launch_constraints",
    "read_from_input",
    "info",
    "get_portfolio",
    "manifest",
    "retry_count",
    "priority",
    "output",
    "output_location",
    "get_current_version",
    "write_result",
    "generate_tasks",
    "generate_provisions",
    "get_launch_tasks_defs",
    "get_task_defs",
]

HEADER = """from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper

"""

global_params = dict(
    account_parameters=dict(),
    associations=list(),
    depends_on=list(),
    iam_role_arns=list(),
    include_expanded_from=False,
    is_dry_run=False,
    launch_constraints=dict(),
    launch_parameters=dict(),
    manifest_parameters=dict(),
    parameters=dict(),
    regions=list(),
    requested_priority=1,
    retry_count=1,
    sharing_policies=dict(),
    should_collect_cloudformation_events=False,
    should_forward_events_to_eventbridge=False,
    should_forward_failures_to_opscenter=False,
    should_use_product_plans=False,
    should_use_sns=False,
    ssm_param_inputs=list(),
    ssm_param_outputs=list(),
    worker_timeout=3,

    assertion_name="assertion_name",
    expected=dict(),
    actual=dict(),

    code_build_run_name="code_build_run_name",
    account_id="account_id",
    cache_invalidator="cache_invalidator",
    execution="execution",
    execution_mode="execution_mode",
    function_name="function_name",
    home_region="home_region",
    invocation_type="invocation_type",
    lambda_invocation_name="lambda_invocation_name",
    launch_name="launch_name",
    manifest_file_path="manifest_file_path",
    name="name",
    organization="organization",
    ou_to_share_with="ou_to_share_with",
    parameter_name="parameter_name",
    permission_boundary="permission_boundary",
    phase="phase",
    portfolio="portfolio",
    portfolio_id="portfolio_id",
    product="product",
    product_generation_method="product_generation_method",
    product_id="product_id",
    project_name="project_name",
    puppet_account_id="puppet_account_id",
    puppet_role_name="puppet_role_name",
    puppet_role_path="puppet_role_path",
    qualifier="qualifier",
    region="region",
    role_name="role_name",
    section="section",
    sharing_mode="sharing_mode",
    single_account="single_account",
    source="source",
    source_type="source_type",
    spoke_local_portfolio_name="spoke_local_portfolio_name",
    stack_name="stack_name",
    type="type",
    version="version",
    version_id="version_id",
    all_params=[],
    try_count=1,
)


def handle_params_for_results_display(f, output):
    returns = list(f.iter_return_stmts())
    if len(returns) != 1:
        raise Exception("unexpected")

    expected = returns[0].get_code()
    open(output, 'a+').write(f"""
    def test_params_for_results_display(self):
        # setup
{expected.replace("return", "expected_result =")}        
    
        # exercise
        actual_result = self.sut.params_for_results_display()
        
        # verify
        self.assertEqual(expected_result, actual_result)
    """)


def handle_api_calls_used(f, output):
    returns = list(f.iter_return_stmts())
    if len(returns) != 1:
        raise Exception("unexpected")

    expected = returns[0].get_code()
    open(output, 'a+').write(f"""
    def test_api_calls_used(self):
        # setup
{expected.replace("return", "expected_result =")}        
    
        # exercise
        actual_result = self.sut.api_calls_used()
        
        # verify
        self.assertEqual(expected_result, actual_result)
    """)


def handle_requires(f, output, mod, classes):
    open(output, 'a+').write(f"""
    @skip
    def test_requires(self):
        # setup
        # exercise
        actual_result = self.sut.requires()

        # verify
        raise NotImplementedError()
    """)


def handle_run(f, output, mod, classes):
    open(output, 'a+').write(f"""
    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
    """)


def handle(c, output, mod, classes):
    for f in c.iter_funcdefs():
        name = f.name.value
        if name == "params_for_results_display":
            handle_params_for_results_display(f, output)
        elif name == "requires":
            handle_requires(f, output, mod, classes)
        elif name == "api_calls_used":
            handle_api_calls_used(f, output)
        elif name == "run":
            handle_run(f, output, mod, classes)
        elif name in ignored:
            pass
        else:
            raise Exception(f"unhandled: {name}")


def handle_function(f, output, mod, classes):
    name = f.name.value
    if name == "params_for_results_display":
        handle_params_for_results_display(f, output)
    elif name == "requires":
        handle_requires(f, output, mod, classes)
    elif name == "api_calls_used":
        handle_api_calls_used(f, output)
    elif name == "run":
        handle_run(f, output, mod, classes)
    elif name in ignored:
        pass
    else:
        raise Exception(f"unhandled: {name}")



# for input in glob.glob("servicecatalog_puppet/workflow/**/*.py", recursive=True):
for input in glob.glob("servicecatalog_puppet/workflow/assertions/**/*.py", recursive=True):
    print(input)
    if input.endswith("_tests.py") or input.endswith("_test.py") or input.endswith(
            "tasks_unit_tests_helper.py") or input.endswith("__init__.py"):
        continue

    print(f"Starting work on {input}")

    code = open(input, 'r').read()
    sut = parso.parse(code, version="3.7")

    output = input.replace(".py", "_test.py")
    code = open(output, 'r').read()
    test = parso.parse(code, version="3.7")

    has_test_requires_already = False
    for c in test.iter_classdefs():
        suite = c.children[-1]
        for child in suite.children:
            if isinstance(child, tree.Function):
                if child.name.value == "test_requires":
                    has_test_requires_already = True

    print(f"has has_test_requires_already={has_test_requires_already}")
    if not has_test_requires_already:
        for c in sut.iter_classdefs():
            suite = c.children[-1]
            for child in suite.children:
                if isinstance(child, tree.Function):
                    if child.name.value == "requires":
                        function = child
                        function.children[1].value = "test_requires"
                        code = function.get_code()
                        code = code.replace("self.", "self.sut.")
                        code = code.replace("    def test_requires(self):", "    def test_requires(self):\n        # setup")
                        code = code.replace("        return requirements", "\n        expected_result = requirements\n        return requirements")
                        code = code.replace("        return requirements", "\n        # exercise\n        actual_result=self.sut.requires()\n        return requirements")
                        code = code.replace("        return requirements", "\n        # assert\n        return requirements")
                        code = code.replace("return requirements", "self.assertEqual(expected_result, actual_result)")
                        print(code)
                    else:
                        continue
