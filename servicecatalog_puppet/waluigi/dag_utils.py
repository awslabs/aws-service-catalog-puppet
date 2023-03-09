#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import logging

import networkx as nx

from servicecatalog_puppet import constants
from servicecatalog_puppet.waluigi.constants import (
    COMPLETED,
    ERRORED,
    NOT_SET,
    QUEUE_STATUS,
)


logger = logging.getLogger(constants.PUPPET_SCHEDULER_LOGGER_NAME)


def build_the_dag(tasks_to_run: dict):
    g = nx.DiGraph()
    # print("-- BUILDING THE DAG!!!")
    for uid, task in tasks_to_run.items():
        g.add_nodes_from(
            [(uid, task),]
        )
        for duid in task.get("dependencies_by_reference", []):
            if tasks_to_run.get(duid):
                g.add_edge(uid, duid)
            else:
                logger.debug(
                    f"{duid} is not in the task reference - this is fine when running in spoke execution mode and when the task was executed within the hub"
                )

    for uid, task in tasks_to_run.items():
        if task.get(QUEUE_STATUS, NOT_SET) == COMPLETED:
            try:
                g.remove_node(uid)
            except nx.exception.NetworkXError as e:
                pass

        elif task.get(QUEUE_STATUS, NOT_SET) == ERRORED:
            # print(
            #     f"looking at task {uid} with status {task.get(QUEUE_STATUS, NOT_SET)}"
            # )
            for n in nx.ancestors(g, uid):
                try:
                    g.remove_node(n)
                except nx.exception.NetworkXError as e:
                    pass
            try:
                g.remove_node(uid)
            except nx.exception.NetworkXError as e:
                pass

    return g


def make_readable_in_codebuild_logs(input):
    numbers = "zero one two three four five six seven eight nine".split()
    numbers.extend("ten eleven twelve thirteen fourteen fifteen sixteen".split())
    numbers.extend("seventeen eighteen nineteen".split())
    numbers.extend(
        tens if ones == "zero" else (tens + "-" + ones)
        for tens in "twenty thirty forty fifty sixty seventy eighty ninety".split()
        for ones in numbers[0:10]
    )
    return numbers[input]
