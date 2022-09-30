#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import serialisation_utils

colors = dict()

default_color = "#88000022"


def generate_node(task_reference, task):
    reference = task_reference.replace("-", "_")
    section_name = task.get("section_name")
    account_id = task.get("account_id")
    region = task.get("region")
    return dict(
        color=colors.get(section_name, default_color),
        label=f"""<table border="0" cellborder="1" cellspacing="0" cellpadding="4">
			<tr> <td colspan='2'> <b>{task_reference}</b></td> </tr>
			<tr> <td align="left">section_name</td> <td>{section_name}</td> </tr>
			<tr> <td align="left">account_id</td> <td>{account_id}</td> </tr>
			<tr> <td align="left">region</td> <td>{region}</td> </tr>
		</table>""",
    )


def escape(input):
    return input.replace("-", "_").replace("/", "__")


def generate_edge(task_reference, dependency_by_reference):
    return f"{escape(task_reference)} -> {escape(dependency_by_reference)}"


def graph(content_file_path):
    content = open(content_file_path.name, "r").read()
    reference = serialisation_utils.load(content)
    all_tasks = reference.get("all_tasks")

    nodes = dict()
    edges = list()

    for task_reference, task in all_tasks.items():
        nodes[task_reference] = generate_node(task_reference, task)
        for dependency_by_reference in task.get("dependencies_by_reference", []):
            edges.append(generate_edge(task_reference, dependency_by_reference))

    nodes_as_a_graph = ""
    for task_reference, node in nodes.items():
        reference = escape(task_reference)
        nodes_as_a_graph += f"""{reference} [
            color="{node.get('color')}"
            label=<{node.get('label')}>
            shape=plain
        ]
        """

    for e in edges:
        nodes_as_a_graph += e + "\n"

    return f"""digraph workflow {{
        {nodes_as_a_graph}
    }}"""
