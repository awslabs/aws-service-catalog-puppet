# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging

logger = logging.getLogger(__name__)


def ext_schema(value, rule_obj, path):
    ensure_deploy_to_tags_exist(value)
    ensure_depends_on_exist(value)
    return True


def ensure_deploy_to_tags_exist(value):
    tags_defined_by_accounts = {}
    for account in value.get("accounts"):
        for tag in account.get("tags"):
            tags_defined_by_accounts[tag] = True

    for collection_type in ["launches", "spoke-local-portfolios"]:
        collection_to_check = value.get(collection_type, [])
        for collection_name, collection_item in collection_to_check.items():
            for deploy_to in collection_item.get("deploy_to", {}).get("tags", []):
                tag_to_check = deploy_to.get("tag")
                if tags_defined_by_accounts.get(tag_to_check) is None:
                    raise AssertionError(
                        f"{collection_type}.{collection_name} uses tag {tag_to_check} in deploy_to that does not exist"
                    )


def ensure_depends_on_exist(value):
    for collection_type in ["launches", "spoke-local-portfolios"]:
        collection_to_check = value.get(collection_type, [])
        for collection_name, collection_item in collection_to_check.items():
            for depends_on in collection_item.get("depends_on", []):
                if value.get("launches").get(depends_on) is None:
                    raise AssertionError(
                        f"{collection_type}.{collection_name} uses {depends_on} in depends_on that does not exist"
                    )
