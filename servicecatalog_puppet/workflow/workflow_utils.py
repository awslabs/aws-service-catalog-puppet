#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import networkx as nx


def ensure_no_cyclic_dependencies(name, tasks):
    g = nx.DiGraph()
    for t_name, t in tasks.items():
        uid = t_name
        data = t
        g.add_nodes_from(
            [(uid, data),]
        )
        for duid in t.get("dependencies_by_reference", []):
            g.add_edge(uid, duid)
    try:
        cycle = nx.find_cycle(g)
        raise Exception(
            f"found cyclic dependency task reference file {name} between: {cycle}"
        )
    except nx.exception.NetworkXNoCycle:
        pass
