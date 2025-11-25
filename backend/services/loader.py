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
    """
    Load the network graph from JSON data files at application startup.
    
    Reads network topology from nodes.json and edges.json in the data/ directory,
    constructs a Graph object representing the fiber optic network, and creates
    a city name-to-ID mapping for easy lookup.
    
    Args:
        edges_path: Path to edges JSON file (default: "data/edges.json")
        nodes_path: Path to nodes JSON file (default: "data/nodes.json")
    
    Returns:
        Graph: Populated graph with all nodes and edges from the data files.
              Nodes include cities, network nodes, regeneration spots, etc.
              Edges include fiber cables with properties like distance, traffic,
              risk, and signal degradation rates.
    
    Side Effects:
        - Writes city_name_to_id.json mapping file to data/ directory
        - Prints loading statistics to console
    """
    g = Graph()

    # Load network topology from JSON files
    with open(nodes_path, "r") as f:
        nodes_data = json.load(f)
    with open(edges_path, "r") as f:
        edges_data = json.load(f)

    print(f"[LOADER] Loading {len(nodes_data)} nodes...")
    
    # Load all nodes first (with empty edge lists, populated later from edges)
    # Track cities separately for easy lookup by name
    city_nodes = []
    node_type_counts = {}
    
    for n in nodes_data:
        node_id = int(n["id"])
        node_name = n.get("name", "")  # City nodes have names, network nodes don't
        node_type = n["type"]
        lat = n["coordinates"]["lat"]
        lng = n["coordinates"]["lng"]
        
        # Count node types
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
        
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
    print(f"[LOADER] Node type counts: {node_type_counts}")
    print(f"[LOADER] Loading {len(edges_data)} edges...")

    # Load all edges and populate node adjacency lists (undirected graph)
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
        
        # Edges with geometry are fiber cables with explicit coordinate paths
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
        
        # Edges without geometry are direct connections (city-to-network links)
        elif not e.get("geometry"):
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
    
    # Verify regeneration spot connectivity
    regen_nodes = [nid for nid, node in g.nodes.items() if node.type == "regen_spot"]
    print(f"[LOADER] Found {len(regen_nodes)} regen_spot nodes")
    if len(regen_nodes) > 0:
        sample_regen = g.nodes[regen_nodes[0]]
        print(f"[LOADER] Sample regen_spot node {regen_nodes[0]}: {len(sample_regen.edge_ids)} edges")
    
    # Save city name mapping for frontend use
    with open("data/city_name_to_id.json", "w") as f:
        json.dump(city_name_to_id, f)

    return g

