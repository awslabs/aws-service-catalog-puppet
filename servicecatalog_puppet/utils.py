#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0


def slugify_for_cloudformation_stack_name(raw) -> str:
    return raw.replace("_", "-")
