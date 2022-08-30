#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
def get_accounts_for_path(client, path):
    ou = client.convert_path_to_ou(path)
    response = client.list_children_nested(ParentId=ou, ChildType="ACCOUNT")
    return ",".join([r.get("Id") for r in response])


macros = {"get_accounts_for_path": get_accounts_for_path}
