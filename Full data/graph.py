import json
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import math

# --- CONFIGURATION ---
NODES_FILE = 'Full data/nodes.json'
EDGES_FILE = 'Full data/edges.json'
START_CITY = "New York"
END_CITY = "Los Angeles"
OUTPUT_IMAGE = "route_visualization.png"

def load_data():
    """Loads nodes and edges from JSON files."""
    print(f"Loading {NODES_FILE} and {EDGES_FILE}...")
    try:
        with open(NODES_FILE, 'r') as f:
            nodes_data = json.load(f)
        with open(EDGES_FILE, 'r') as f:
            edges_data = json.load(f)
        return nodes_data, edges_data
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return [], []

def build_graph(nodes_data, edges_data):
    """Constructs a NetworkX graph from the data."""
    print("Building network graph...")
    G = nx.Graph()
    
    # Add nodes with attributes
    for node in nodes_data:
        G.add_node(node['id'], **node)
        
    # Add edges with weights
    for edge in edges_data:
        # Use existing weight or default to 1
        w = edge.get('weight', 1.0)
        # Avoid passing 'weight' twice (once explicitly and possibly inside edge dict)
        attrs = {k: v for k, v in edge.items() if k not in ('source', 'target', 'weight')}
        G.add_edge(edge['source'], edge['target'], weight=w, **attrs)
        
    return G

def get_node_id_by_name(nodes_data, city_name):
    """Finds the ID of a city node by its name."""
    for node in nodes_data:
        if node.get('type') == 'city' and node.get('name') == city_name:
            return node['id']
    return None

def plot_route(G, path_nodes, nodes_data, start_name, end_name, total_dist):
    """Plots the entire map and highlights the specific route."""
    print("Plotting map...")
    
    # 1. Extract coordinates for all nodes for quick lookup
    pos = {}
    for node in nodes_data:
        coords = node.get('coordinates', {})
        # Matplotlib expects (x, y) -> (lng, lat)
        pos[node['id']] = (coords.get('lng'), coords.get('lat'))

    # 2. Prepare background lines (The entire US Network)
    bg_segments = []
    for u, v in G.edges():
        if u in pos and v in pos:
            bg_segments.append([pos[u], pos[v]])
            
    # 3. Prepare Path lines (The specific route found)
    path_segments = []
    if path_nodes:
        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i+1]
            if u in pos and v in pos:
                path_segments.append([pos[u], pos[v]])

    # 4. Setup Plot
    fig, ax = plt.subplots(figsize=(20, 12), facecolor='#f8f9fa')
    ax.set_facecolor('white')
    
    # Draw Background Network (Gray)
    lc_bg = LineCollection(bg_segments, colors='#e0e0e0', linewidths=0.8, alpha=0.6, zorder=1)
    ax.add_collection(lc_bg)
    
    # Draw The Route (Blue/Purple gradient style)
    if path_segments:
        lc_path = LineCollection(path_segments, colors='#3b82f6', linewidths=2.5, alpha=1.0, zorder=3)
        ax.add_collection(lc_path)
    
    # 5. Draw Cities (Stars)
    # Filter only cities to reduce clutter
    city_x = [pos[n['id']][0] for n in nodes_data if n.get('type') == 'city']
    city_y = [pos[n['id']][1] for n in nodes_data if n.get('type') == 'city']
    ax.scatter(city_x, city_y, c='#ef4444', s=30, marker='*', zorder=2, alpha=0.6, label='Other Cities')

    # 6. Highlight Start and End
    if path_nodes:
        start_id = path_nodes[0]
        end_id = path_nodes[-1]
        
        sx, sy = pos[start_id]
        ex, ey = pos[end_id]
        
        # Start (Green)
        ax.scatter([sx], [sy], c='#22c55e', s=200, marker='o', edgecolors='black', zorder=5, label='Start')
        ax.annotate(start_name, (sx, sy), xytext=(10, 10), textcoords='offset points', fontsize=12, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.8))
        
        # End (Red)
        ax.scatter([ex], [ey], c='#dc2626', s=200, marker='X', edgecolors='black', zorder=5, label='Destination')
        ax.annotate(end_name, (ex, ey), xytext=(10, 10), textcoords='offset points', fontsize=12, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.8))

    # Formatting
    plt.title(f"Route: {start_name} to {end_name}\nDistance: {total_dist:.1f} km", fontsize=16, pad=20)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.axis('equal') # Maintain map aspect ratio
    
    # Auto-scale view to fit the US (or the route)
    # We set a fixed aspect for US broadly
    ax.set_xlim(-128, -65)
    ax.set_ylim(24, 50)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=150)
    print(f"✅ Map saved to {OUTPUT_IMAGE}")
    # plt.show() # Uncomment if you want to see it pop up

def main():
    # 1. Load
    nodes, edges = load_data()
    if not nodes: return

    # 2. Build Graph
    G = build_graph(nodes, edges)

    # 3. Find Start/End IDs
    start_id = get_node_id_by_name(nodes, START_CITY)
    end_id = get_node_id_by_name(nodes, END_CITY)

    if not start_id:
        print(f"❌ Could not find city: {START_CITY}")
        return
    if not end_id:
        print(f"❌ Could not find city: {END_CITY}")
        return

    print(f"Finding shortest path from {START_CITY} ({start_id}) to {END_CITY} ({end_id})...")

    # 4. Calculate Path (Dijkstra)
    try:
        path = nx.shortest_path(G, source=start_id, target=end_id, weight='weight')
        dist = nx.shortest_path_length(G, source=start_id, target=end_id, weight='weight')
        print(f"🎉 Path found! Nodes: {len(path)}, Distance: {dist:.2f} km")
        
        # 5. Visualize
        plot_route(G, path, nodes, START_CITY, END_CITY, dist)
        
    except nx.NetworkXNoPath:
        print("❌ No path found between these cities!")

if __name__ == "__main__":
    main()