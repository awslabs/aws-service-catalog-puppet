#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import click

from servicecatalog_puppet import config
from servicecatalog_puppet.commands.misc import generate_tasks
from servicecatalog_puppet.workflow import tasks as puppet_tasks


def graph_nodes(what):
    nodes = []
    if isinstance(what, puppet_tasks.PuppetTask):
        nodes.append(what.graph_node())
        nodes += graph_nodes(what.requires())
    elif isinstance(what, list):
        for i in what:
            nodes += graph_nodes(i)
    elif isinstance(what, dict):
        for i in what.values():
            nodes += graph_nodes(i)
    else:
        raise Exception(f"unknown {type(what)}")
    return nodes


def graph_lines(task, dependency):
    nodes = []
    if isinstance(dependency, puppet_tasks.PuppetTask):
        nodes.append(f'"{task.node_id}" -> "{dependency.node_id}"')
        # nodes += graph_lines(task, task.requires())
    elif isinstance(dependency, list):
        for i in dependency:
            nodes += graph_lines(task, i)
    elif isinstance(dependency, dict):
        for i in dependency.values():
            nodes += graph_lines(task, i)
    else:
        raise Exception(f"unknown {type(dependency)}")
    return nodes


def graph(f):
    current_account_id = puppet_account_id = config.get_puppet_account_id()
    tasks_to_run = generate_tasks(f, puppet_account_id, current_account_id)
    lines = []
    nodes = []
    for task in tasks_to_run:
        nodes += graph_nodes(task)

        what = task.requires()
        if isinstance(what, puppet_tasks.PuppetTask):
            lines.append(f'"{task.node_id}" -> "{what.node_id}"')
        elif isinstance(what, list):
            for item in what:
                lines += graph_lines(task, item)
        elif isinstance(what, dict):
            for item in what.values():
                lines += graph_lines(task, item)
        else:
            raise Exception(f"unknown {type(what)}")

        # nodes.append(task.graph_node())
        # lines += task.get_graph_lines()
    click.echo("digraph G {\n")
    click.echo("node [shape=record fontname=Arial];")
    for node in nodes:
        click.echo(f"{node};")
    for line in lines:
        click.echo(f'{line} [label="depends on"];')
    click.echo("}")
