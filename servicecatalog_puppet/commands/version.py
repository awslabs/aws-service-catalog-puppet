#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import click
import pkg_resources
from betterboto import client as betterboto_client


def version():
    click.echo(
        "cli version: {}".format(
            pkg_resources.require("aws-service-catalog-puppet")[0].version
        )
    )
    with betterboto_client.ClientContextManager("ssm") as ssm:
        response = ssm.get_parameter(Name="service-catalog-puppet-regional-version")
        click.echo(
            "regional stack version: {} for region: {}".format(
                response.get("Parameter").get("Value"),
                response.get("Parameter").get("ARN").split(":")[3],
            )
        )
        response = ssm.get_parameter(Name="service-catalog-puppet-version")
        click.echo("stack version: {}".format(response.get("Parameter").get("Value"),))
