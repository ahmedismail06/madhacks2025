# ===========================================
# services/loader.py — load nodes.json and edges.json on startup
# ===========================================

import json
from os import path
from core.graph import Graph, Node, Edge

global city_name_to_id 
city_name_to_id = {}  # mapping of city names to node IDs
# save the dictionary to an external file at the end of loading

def load_graph(edges_path="data/edges.json", nodes_path="data/nodes.json") -> Graph:
    g = Graph()

    with open(nodes_path, "r") as f:
        nodes_data = json.load(f)
    with open(edges_path, "r") as f:
        edges_data = json.load(f)

    # Load all nodes first (with empty edge lists initially)
    # nodes.json is an array, not an object with "nodes" key
    for n in nodes_data:
        node_id = int(n["id"])
        node_name = n.get("name", "")  # City nodes have names, network nodes don't
        node_type = n["type"]
        lat = n["coordinates"]["lat"]
        lng = n["coordinates"]["lng"]
        
        # Track city names for lookup
        if node_name:
            city_name_to_id[node_name] = node_id
        
        node = Node(
            id=node_id,
            name=node_name,
            node_type=node_type,
            x=lat,
            y=lng,
            edge_ids=[]  # Start with empty list, will populate from edges
        )
        g.add_node(node)

    # Load all edges and add them to both connected nodes (undirected graph)
    # edges.json is an array, not an object with "edges" key
    for e in edges_data:
        edge_id = int(e["id"])
        source_id = int(e["source"])
        target_id = int(e["target"])
        
        # Extract geometry coordinates if available, if not then skip the edge
        if "geometry" in e and e["geometry"]:
            coords = e["geometry"]
            start_x, start_y = coords[0]
            end_x, end_y = coords[-1]
        
            edge = Edge(
                id=edge_id,
                from_node=source_id,
                to_node=target_id,
                distance=e.get("weight", 1.0),
                traffic_load=e.get("traffic_load", 0.5),
                base_ms=e.get("base_ms", 0.003),
                risk=e.get("risk", 0.05),
                degrade_rate=e.get("degrade_rate", 0.025),
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y
            )
            g.add_edge(edge)
        
            # Add edge to both nodes (undirected graph)
            if source_id in g.nodes:
                g.nodes[source_id].edge_ids.append(edge_id)
            if target_id in g.nodes:
                g.nodes[target_id].edge_ids.append(edge_id)
    
    # Save the city_name_to_id dictionary to an external file
    with open("data/city_name_to_id.json", "w") as f:
        json.dump(city_name_to_id, f)

    return g

