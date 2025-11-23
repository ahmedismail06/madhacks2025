import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd  # <--- Added to read your CSV

# CONFIGURATION
INPUT_FILE = "../../game_map_data.json"
INTERSECTIONS_FILE = "mainland_intersections.csv"  # <--- The points we generated

def visualize():
    # --- 1. Load Game Data (JSON) ---
    print(f"Loading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "r") as f:
            data = json.load(f)
        nodes = data['nodes']
        edges = data['edges']
    except FileNotFoundError:
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    # --- 2. Load Intersection Data (CSV) ---
    print(f"Loading {INTERSECTIONS_FILE}...")
    try:
        df_intersections = pd.read_csv(INTERSECTIONS_FILE)
        # Filter strictly to mainland logic if not already filtered, 
        # but we assume the CSV is the clean one.
        ix_x = df_intersections['lon']
        ix_y = df_intersections['lat']
        print(f"   Loaded {len(df_intersections)} highway intersections.")
    except FileNotFoundError:
        print(f"⚠️ Warning: {INTERSECTIONS_FILE} not found. Skipping overlay.")
        ix_x, ix_y = [], []

    print(f"Plotting {len(nodes)} game nodes and {len(edges)} edges...")

    # Create Dictionary for fast coordinate lookup
    node_coords = {n['id']: (n['lng'], n['lat']) for n in nodes}
    
    # Separate Nodes by Type for separate styling
    cities_x, cities_y = [], []
    regen_x, regen_y = [], []
    routing_x, routing_y = [], []

    for n in nodes:
        coords = node_coords.get(n['id'])
        if coords:
            if n.get('type') == 'city':
                cities_x.append(coords[0])
                cities_y.append(coords[1])
            elif n.get('type') == 'regen':
                regen_x.append(coords[0])
                regen_y.append(coords[1])
            else:
                routing_x.append(coords[0])
                routing_y.append(coords[1])

    # Setup Plot
    fig, ax = plt.subplots(figsize=(15, 10))
    fig.patch.set_facecolor('#1e1e1e') # Dark background
    ax.set_facecolor('#1e1e1e')

    # --- PLOT 0: RAW INTERSECTIONS (Background Layer) ---
    # We plot these first (lowest zorder) so they sit behind the game elements
    if len(ix_x) > 0:
        ax.scatter(ix_x, ix_y, 
                   color='white', 
                   s=0.5,       # Very small dots
                   alpha=0.15,  # Very faint
                   label='Highway Network', 
                   zorder=0)

    # --- PLOT 1: EDGES ---
    cmap = plt.cm.get_cmap('coolwarm') 
    norm = mcolors.Normalize(vmin=0.0, vmax=0.3)

    for e in edges:
        if e['from'] in node_coords and e['to'] in node_coords:
            p1 = node_coords[e['from']]
            p2 = node_coords[e['to']]
            
            risk_color = cmap(norm(e.get('risk', 0))) # Default to 0 risk if missing
            
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 
                    color=risk_color, 
                    linewidth=0.8, 
                    alpha=0.6,
                    zorder=1)

    # --- PLOT 2: GAME NODES ---
    # Routing Nodes
    ax.scatter(routing_x, routing_y, color='Red', s=5, alpha=0.5, label='Routing Node', zorder=2)
    
    # Regen Spots 
    # ax.scatter(regen_x, regen_y, c='#00ffcc', s=15, alpha=0.8, label='Regen Station', zorder=3)
    
    # Cities 
    # ax.scatter(cities_x, cities_y, c='#ffcc00', s=60, edgecolors='black', label='City', zorder=4)

    # Styling
    ax.set_title("Game Map Network", color='white', fontsize=16)
    ax.set_aspect('equal')
    ax.axis('off') 
    
    # Legend
    leg = ax.legend(facecolor='#333333', edgecolor='white', loc='lower right')
    for text in leg.get_texts():
        text.set_color("white")
    
    # Adjust zoom to fit the points if you want auto-zoom
    # ax.autoscale()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    visualize()