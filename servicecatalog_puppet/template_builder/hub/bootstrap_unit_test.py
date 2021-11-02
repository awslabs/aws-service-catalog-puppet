#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0


def test_codecommit_provider():
    # setup
    from . import bootstrap

    puppet_version = "0.10.0"
    all_regions = [
        "us-east-1",
        "us-east-2",
    ]
    repo_name = "TestRepoName"
    repo_branch = "mainly"
    source = dict(
        Provider="CodeCommit",
        Configuration=dict(RepositoryName=repo_name, BranchName=repo_branch),
    )
    is_caching_enabled = False
    is_manual_approvals = False
    scm_skip_creation_of_repo = False
    should_validate = False

    # exercise
    actual_result = bootstrap.get_template(
        puppet_version,
        all_regions,
        source,
        is_caching_enabled,
        is_manual_approvals,
        scm_skip_creation_of_repo,
        should_validate,
    )

    source_stage = actual_result.resources.get("Pipeline").Stages[0]
    action = source_stage.Actions[1]

    # verify
    assert source_stage.Name == "Source"
    assert action.ActionTypeId.Provider == "CodeCommit"
    assert actual_result.resources.get("CodeRepo").RepositoryName == repo_name
    assert action.Configuration.get("BranchName") == repo_branch
