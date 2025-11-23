# ===========================================
# services/loader.py — load graph.json on startup
# ===========================================

import json
from core.graph import Graph, Node, Edge

global city_name_to_id 
city_name_to_id = {}

def load_graph(path="data/graph.json") -> Graph:
    g = Graph()
    with open(path, "r") as f:
        data = json.load(f)

    # data format expected:
    # { "nodes": [...], "edges": [...] }

    # Load all nodes first
    for n in data["nodes"]:
        if n["type"] == "city":
            city_name_to_id[n["name"]] = n["id"]
        node = Node(
            id=n["id"],
            name=n["name"],
            node_type=n["type"],
            lat=n["lat"],
            lng=n["lng"],
            edge_ids=n["edges"]
        )
        g.add_node(node)

    # Load all edges
    for e in data["edges"]:
        edge = Edge(
            id=e["id"],
            from_node=e["from"],
            to_node=e["to"],
            distance=e["distance"],
            cost=e["cost"],
            risk=e["risk"],
            degrade_rate=e["degrade_rate"]
        )
        g.add_edge(edge)

    return g

