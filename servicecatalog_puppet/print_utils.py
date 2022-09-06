#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import click


def echo(message):
    click.secho(message,)


def warn(message):
    click.secho(
        message, err=True, fg="yellow",
    )


def error(message):
    click.secho(
        message, err=True, fg="red",
    )
