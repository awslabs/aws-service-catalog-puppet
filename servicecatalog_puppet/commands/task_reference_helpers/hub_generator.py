#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import serialisation_utils, constants
from servicecatalog_puppet.workflow import workflow_utils


def generate(puppet_account_id, all_tasks, output_file_path):
    tasks_to_include = dict()
    generate_manifest_ref = "generate-manifest"
    for task_name, task in all_tasks.get("all_tasks").items():
        execution = task.get("execution", constants.EXECUTION_MODE_DEFAULT)
        if execution in [constants.EXECUTION_MODE_HUB, constants.EXECUTION_MODE_ASYNC]:
            should_include = True
        elif execution == constants.EXECUTION_MODE_SPOKE:
            # should_include = False
            # sharing should happen from the hub for launches in spoke mode
            should_include = (
                task.get("section_name") == constants.PORTFOLIO_SHARE_AND_ACCEPT_ACCOUNT
            )

        elif execution == constants.EXECUTION_MODE_HUB_AND_SPOKE_SPLIT:
            # cannot assume account_id role from spoke when it is the puppet account id
            should_include = (
                task.get("account_id", puppet_account_id) == puppet_account_id
            )
            # these should not override the previous decisions
            if not should_include:
                # sharing should happen from the hub for spoke-local-portfolios in hub and spoke split mode
                should_include = task.get("section_name") in [
                    constants.PORTFOLIO_SHARE_AND_ACCEPT_ACCOUNT,
                    constants.PORTFOLIO_SHARE_AND_ACCEPT_AWS_ORGANIZATIONS,
                ]
        else:
            raise Exception("Unhandled execution")

        if should_include:
            tasks_to_include[task_name] = task
        else:
            if not tasks_to_include.get(generate_manifest_ref):
                tasks_to_include[generate_manifest_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    task_reference=generate_manifest_ref,
                    section_name=constants.GENERATE_MANIFEST,
                    dependencies_by_reference=[],
                )

            replacement_ref = (
                f"{constants.RUN_DEPLOY_IN_SPOKE}_{task.get('account_id')}"
            )
            if not tasks_to_include.get(replacement_ref):
                tasks_to_include[replacement_ref] = dict(
                    execution=constants.EXECUTION_MODE_HUB,
                    puppet_account_id=puppet_account_id,
                    account_id=task.get("account_id"),
                    section_name=constants.RUN_DEPLOY_IN_SPOKE,
                    task_reference=replacement_ref,
                    generate_manifest_ref=generate_manifest_ref,
                    dependencies_by_reference=[generate_manifest_ref,],
                )

    # make sure everything runs before we zip up the output directory
    if tasks_to_include.get(generate_manifest_ref):
        t = tasks_to_include[generate_manifest_ref]
        for task_name, task_to_include in tasks_to_include.items():
            if task_to_include.get("section_name") not in [
                constants.RUN_DEPLOY_IN_SPOKE,
                constants.GENERATE_MANIFEST,
            ]:
                t["dependencies_by_reference"].append(task_name)

    for task_name, task_to_include in tasks_to_include.items():
        for dep in task_to_include.get("dependencies_by_reference"):
            if not tasks_to_include.get(dep):
                raise Exception(
                    f"{task_name} depends on: {dep} which is not listed in this reference"
                )

    result = dict(all_tasks=tasks_to_include)
    workflow_utils.ensure_no_cyclic_dependencies("hub task reference", tasks_to_include)
    # open(output_file_path, "w").write(serialisation_utils.dump(result))
    open(output_file_path, "w").write(serialisation_utils.dump_as_json(result))
    return result
