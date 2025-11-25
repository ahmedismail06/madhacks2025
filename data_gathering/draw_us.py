import json
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

# CONFIGURATION
NODES_FILE = 'nodes.json'
EDGES_FILE = 'edges.json'
OUTPUT_IMAGE = 'network_structure.png'

def main():
    print(f"Loading {NODES_FILE} and {EDGES_FILE}...")
    try:
        with open(NODES_FILE, 'r') as f:
            nodes_data = json.load(f)
        with open(EDGES_FILE, 'r') as f:
            edges_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # 1. Map Node IDs to Coordinates (Longitude, Latitude)
    print("Mapping node coordinates...")
    node_coords = {}
    city_nodes = []
    
    for node in nodes_data:
        nid = node['id']
        # Matplotlib plots (x, y), so we use (lng, lat)
        coords = (node['coordinates']['lng'], node['coordinates']['lat'])
        node_coords[nid] = coords
        
        # Only mark actual cities (User previously had 'routing_node' here which might be noisy)
        if node.get('type') == 'city':
            city_nodes.append(coords)

    # 2. Build Edge Segments (Start -> End)
    # This ignores the detailed 'geometry' curve and just draws the structural link
    print("Building edge segments...")
    segments = []
    skipped_edges = 0
    filtered_edges = 0

    for edge in edges_data:
        u = edge['source']
        v = edge['target']
        
        if u in node_coords and v in node_coords:
            p1 = node_coords[u]
            p2 = node_coords[v]
            
            # --- FILTER: Remove Non-Continental Artifacts ---
            # Puerto Rico is ~Lat 18. Key West (Southernmost continental US point) is ~Lat 24.5.
            # We filter out any edge that goes south of Lat 24.0 to remove the "Florida stick".
            lat1, lat2 = p1[1], p2[1]
            
            if lat1 < 24.0 or lat2 < 24.0:
                filtered_edges += 1
                continue

            segments.append([p1, p2])
        else:
            skipped_edges += 1

    if skipped_edges > 0:
        print(f"Warning: Skipped {skipped_edges} edges due to missing nodes.")
    if filtered_edges > 0:
        print(f"ℹ️  Removed {filtered_edges} edges to clean up the map (e.g. Puerto Rico links).")

    # 3. Plotting
    print("Generating plot...")
    fig, ax = plt.subplots(figsize=(20, 12), facecolor='white')
    ax.set_facecolor('#111111') # Dark background for high contrast

    # Plot Edges
    # We use a LineCollection for high performance with thousands of lines
    lc = LineCollection(segments, colors="black", linewidths=0.5, alpha=0.6)
    ax.add_collection(lc)

    # Plot Cities (Bright Red Stars)
#     if city_nodes:
#         city_x = [c[0] for c in city_nodes]
#         city_y = [c[1] for c in city_nodes]
#         ax.scatter(city_x, city_y, c='#ff3333', s=15, marker='o', zorder=10, label='Cities')

    # Formatting
    ax.autoscale()
    ax.set_aspect('equal')
    ax.axis('off') # Hide axes for a clean look
    plt.title(f"Network Connectivity ({len(segments)} edges)", color='black', pad=20)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✅ Image saved to {OUTPUT_IMAGE}")

if __name__ == "__main__":
    main()