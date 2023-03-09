#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

    is_directed_acyclic_graph = nx.is_directed_acyclic_graph(g)
    if not is_directed_acyclic_graph:
        print(
            f"Generated graph is not a DAG, looking for cycles to help debug (this may take 1 - 2 hours)"
        )
        try:
            cycle = nx.find_cycle(g)
            raise Exception(
                f"found cyclic dependency task reference file {name} between: {cycle}"
            )
        except nx.exception.NetworkXNoCycle:
            pass
        raise Exception(
            "Generated graph is not a DAG but could not find cycles to help debug."
        )
