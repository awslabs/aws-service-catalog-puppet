#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import utils


def generate_stack_name_for_associations_by_item_name(item_name):
    return (
        f"associations-v2-for-{utils.slugify_for_cloudformation_stack_name(item_name)}"
    )
