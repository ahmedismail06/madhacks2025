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

    print(f"[LOADER] Loading {len(nodes_data)} nodes...")
    
    # Load all nodes first (with empty edge lists initially)
    # nodes.json is an array, not an object with "nodes" key
    city_nodes = []
    for n in nodes_data:
        node_id = int(n["id"])
        node_name = n.get("name", "")  # City nodes have names, network nodes don't
        node_type = n["type"]
        lat = n["coordinates"]["lat"]
        lng = n["coordinates"]["lng"]
        
        # Track city names for lookup
        if node_name:
            city_name_to_id[node_name] = node_id
            city_nodes.append(node_name)
        
        node = Node(
            id=node_id,
            name=node_name,
            node_type=node_type,
            x=lat,
            y=lng,
            edge_ids=[]  # Start with empty list, will populate from edges
        )
        g.add_node(node)
    
    print(f"[LOADER] Loaded {len(city_nodes)} cities: {city_nodes[:5]}...")
    print(f"[LOADER] Loading {len(edges_data)} edges...")

    # Load all edges and add them to both connected nodes (undirected graph)
    # edges.json is an array, not an object with "edges" key
    edges_with_geometry = 0
    edges_road_connection = 0
    edges_skipped = 0
    
    for e in edges_data:
        edge_id = int(e["id"])
        source_id = int(e["source"])
        target_id = int(e["target"])
        
        # Check if both nodes exist
        if source_id not in g.nodes or target_id not in g.nodes:
            edges_skipped += 1
            continue
        
        # Extract geometry coordinates if available, if not, check if city connection
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
            edges_with_geometry += 1
        
            # Add edge to both nodes (undirected graph)
            if source_id in g.nodes:
                g.nodes[source_id].edge_ids.append(edge_id)
            if target_id in g.nodes:
                g.nodes[target_id].edge_ids.append(edge_id)
        
        elif e.get("road_name", "").startswith("Road connection"):
            # This is a city-to-network connection without geometry
            edge = Edge(
                id=edge_id,
                from_node=source_id,
                to_node=target_id,
                distance=e.get("weight", 1.0),
                traffic_load=e.get("traffic_load", 0.5),
                base_ms=e.get("base_ms", 0.003),
                risk=e.get("risk", 0.05),
                degrade_rate=e.get("degrade_rate", 0.025),
                start_x=g.nodes[source_id].x,
                start_y=g.nodes[source_id].y,
                end_x=g.nodes[target_id].x,
                end_y=g.nodes[target_id].y
            )
            g.add_edge(edge)
            edges_road_connection += 1
        
            # Add edge to both nodes (undirected graph)
            if source_id in g.nodes:
                g.nodes[source_id].edge_ids.append(edge_id)
            if target_id in g.nodes:
                g.nodes[target_id].edge_ids.append(edge_id)
        else:
            edges_skipped += 1

    print(f"[LOADER] Loaded {edges_with_geometry} edges with geometry")
    print(f"[LOADER] Loaded {edges_road_connection} road connection edges")
    print(f"[LOADER] Skipped {edges_skipped} edges")
    
    # Print sample city edge counts
    for city_name in list(city_name_to_id.keys())[:3]:
        city_id = city_name_to_id[city_name]
        edge_count = len(g.nodes[city_id].edge_ids)
        print(f"[LOADER] City '{city_name}' (ID: {city_id}) has {edge_count} edges")


    # Save the city_name_to_id dictionary to an external file
    with open("data/city_name_to_id.json", "w") as f:
        json.dump(city_name_to_id, f)

    return g

