#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import jinja2

from servicecatalog_puppet.asset_helpers import resolve_from_site_packages

TEMPLATE_DIR = resolve_from_site_packages("templates")


def slugify_for_cloudformation_stack_name(raw) -> str:
    return raw.replace("_", "-")


ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR), extensions=["jinja2.ext.do"],
)
