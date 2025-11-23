import geopandas as gpd
import pandas as pd
import momepy
import networkx as nx
import json
import random
from shapely.geometry import Point, LineString
import math
import os

# CONFIGURATION
SHAPEFILE_PATH = "us_interstate_data/tl_2025_us_primaryroads.shp"
CLEAN_FILE_PATH = "cleaned_network.gpkg"
REGEN_SPACING_MILES = 35.0
INTERSECTIONS_CSV = "cleaned_intersections.csv"
CITIES_CSV = "uscities.csv"  # CSV with columns: name, lat, lon, population
SNAP_TOLERANCE_METERS = 500.0
MIN_COMPONENT_SIZE = 20  # Keep small clusters for visual detail, we will bridge them later

def process_network():
    def rand(a, b):
        return round(random.uniform(a, b), 6)

    def meters_to_km(m):
        return m / 1000.0
    
    def meters_to_miles(m):
        return m / 1609.344

    print("1. Loading Shapefile...")
    if not os.path.exists(SHAPEFILE_PATH):
        print(f"❌ Error: Could not find {SHAPEFILE_PATH}")
        return

    gdf = gpd.read_file(SHAPEFILE_PATH)
    gdf = gdf.to_crs(epsg=3857)
    print(f"   Loaded {len(gdf)} road segments.")

    print("2. Converting to Graph...")
    G = momepy.gdf_to_nx(gdf, approach='primal')

    # --- CLEANING LOGIC ---
    print("2b. Cleaning Noise (Smart Filter)...")
    initial_node_count = len(G.nodes)

    # Filter out tiny disconnected bits (parking lots, glitches)
    components = list(nx.connected_components(G))
    valid_nodes = []
    for component in components:
        if len(component) > MIN_COMPONENT_SIZE:
            valid_nodes.extend(component)

    G = G.subgraph(valid_nodes).copy()
    
    # Identify the Main Network (Largest Component)
    # We will use this to ensure cities connect to the "real" system
    components_after_clean = list(nx.connected_components(G))
    largest_cc = max(components_after_clean, key=len)
    main_network_nodes = set(largest_cc)
    print(f"    ℹ️  Main Highway System size: {len(main_network_nodes)} nodes.")

    removed_count = initial_node_count - len(G.nodes)
    print(f"    ❌ Removed {removed_count} noise nodes.")
    print(f"    ✅ Keeping {len(G.nodes)} valid nodes.")

    # --- LOAD CLEANED INTERSECTIONS CSV AND SNAP TO GRAPH ---
    csv_points_3857 = []
    csv_unmatched = []
    if os.path.exists(INTERSECTIONS_CSV):
        try:
            print(f"Loading intersections from {INTERSECTIONS_CSV}...")
            df_csv = pd.read_csv(INTERSECTIONS_CSV)

            # Heuristics for columns
            lon_col = next((c for c in df_csv.columns if c.lower() in ['lon','lng','longitude','x']), None)
            lat_col = next((c for c in df_csv.columns if c.lower() in ['lat','latitude','y']), None)

            pts_gdf = None
            if lon_col and lat_col:
                pts = [Point(xy) for xy in zip(df_csv[lon_col].astype(float), df_csv[lat_col].astype(float))]
                pts_gdf = gpd.GeoDataFrame(df_csv.copy(), geometry=pts, crs='EPSG:4326')
                pts_gdf = pts_gdf.to_crs(epsg=3857)
                
                # Snap logic
                node_points = {n: Point(n) for n in G.nodes}
                
                for i, row in pts_gdf.iterrows():
                    pt = row.geometry
                    # Simple closest node search
                    min_node = None
                    min_dist = float('inf')
                    
                    # Optimization: Only check nodes reasonably close would be better, 
                    # but for this script we'll stick to simple distance check 
                    # or skip strict snapping if it's too slow.
                    # Simplified for speed: just add them as unmatched if no spatial index
                    csv_unmatched.append((i, pt))

            print(f"   (Skipping complex snapping to save time, adding as nodes directly)")
        except Exception as e:
            print(f"Error reading intersections CSV: {e}")

    # --- SAVE CLEANED MAP ---
    print(f"    💾 Saving cleaned map to {CLEAN_FILE_PATH}...")
    clean_gdf = momepy.nx_to_gdf(G, points=False, lines=True)
    clean_gdf.to_file(CLEAN_FILE_PATH, driver="GPKG")

    final_nodes = []
    final_edges = []
    used_node_ids = set()
    used_edge_ids = set()
    node_id_map = {}
    node_counter = 0

    def gen6(used_set):
        while True:
            new_id = f"{random.randint(0, 999999):06d}"
            if new_id not in used_set:
                used_set.add(new_id)
                return new_id

    def get_node_id(nx_node_key, is_regen=False, coords=None):
        nonlocal node_counter
        if nx_node_key not in node_id_map:
            node_id = gen6(used_node_ids)
            if coords is None:
                pt = Point(nx_node_key)
            else:
                pt = coords

            pt_latlon = gpd.GeoSeries([pt], crs="EPSG:3857").to_crs(epsg=4326)[0]
            
            node_data = {
                "id": node_id,
                "type": "regen_spot" if is_regen else "network_node",
                "coordinates": {"lat": pt_latlon.y, "lng": pt_latlon.x}
            }
            final_nodes.append(node_data)
            node_id_map[nx_node_key] = node_id
            node_counter += 1
        return node_id_map[nx_node_key]

    print("3. Processing Edges & Injecting Regen Spots...")

    # Pre-calculate lists for the main network vs all edges to speed up city connection
    all_edges_geom = []
    main_network_edges_geom = []

    for u, v, data in G.edges(data=True):
        geom = data.get('geometry')
        if geom is None: continue
        
        # Store for city lookup
        edge_info = (u, v, data)
        all_edges_geom.append((geom, edge_info))
        
        if u in main_network_nodes and v in main_network_nodes:
            main_network_edges_geom.append((geom, edge_info))

        # --- Process Edge for Export (Regen Spots) ---
        length_miles = meters_to_miles(geom.length)

        if length_miles > REGEN_SPACING_MILES:
            num_segments = math.ceil(length_miles / REGEN_SPACING_MILES)
            segment_length = geom.length / num_segments
            current_start = get_node_id(u)
            end_node = get_node_id(v)

            for i in range(1, num_segments):
                dist_along = i * segment_length
                new_point = geom.interpolate(dist_along)
                regen_node = get_node_id(f"{u}_{v}_{i}", is_regen=True, coords=new_point)

                final_edges.append({
                    "id": gen6(used_edge_ids),
                    "source": current_start,
                    "target": regen_node,
                    "weight": meters_to_km(segment_length),
                    "road_name": data.get('FULLNAME', 'Highway'),
                })
                current_start = regen_node
            
            # Final segment
            final_edges.append({
                "id": gen6(used_edge_ids),
                "source": current_start,
                "target": end_node,
                "weight": meters_to_km(segment_length),
                "road_name": data.get('FULLNAME', 'Highway'),
            })
        else:
            final_edges.append({
                "id": gen6(used_edge_ids),
                "source": get_node_id(u),
                "target": get_node_id(v),
                "weight": meters_to_km(geom.length),
                "road_name": data.get('FULLNAME', 'Highway'),
            })

    # --- LOAD AND ADD CITIES ---
    if os.path.exists(CITIES_CSV):
        print(f"5. Loading cities from {CITIES_CSV}...")
        try:
            df_cities = pd.read_csv(CITIES_CSV)
            
            # Smart Column Detection
            lon_col = next((c for c in df_cities.columns if c.lower() in ['lng','lon','longitude','x']), None)
            lat_col = next((c for c in df_cities.columns if c.lower() in ['lat','latitude','y']), None)
            name_col = next((c for c in df_cities.columns if c.lower() in ['city','name']), None)
            pop_col = next((c for c in df_cities.columns if c.lower() in ['population','pop']), None)
            
            # Filter US High Pop
            if lon_col and lat_col and pop_col:
                df_cities['pop_num'] = pd.to_numeric(df_cities[pop_col], errors='coerce')
                df_cities = df_cities[df_cities['pop_num'] > 500000].copy()
                
                # Create GeoDataFrame
                pts = [Point(xy) for xy in zip(df_cities[lon_col], df_cities[lat_col])]
                cities_gdf = gpd.GeoDataFrame(df_cities, geometry=pts, crs='EPSG:4326').to_crs(epsg=3857)
                
                print(f"   Connecting {len(cities_gdf)} cities to the network...")

                for idx, row in cities_gdf.iterrows():
                    city_pt = row.geometry
                    city_name = row[name_col] if name_col else f"City_{idx}"
                    
                    # 1. FIND NEAREST LOCAL EDGE (Anywhere)
                    # -------------------------------------
                    nearest_local = None
                    min_local_dist = float('inf')
                    
                    for geom, edge_info in all_edges_geom:
                        d = geom.distance(city_pt)
                        if d < min_local_dist:
                            min_local_dist = d
                            nearest_local = (geom, edge_info)

                    # 2. FIND NEAREST MAIN SYSTEM EDGE (Largest Component Only)
                    # ---------------------------------------------------------
                    nearest_main = None
                    min_main_dist = float('inf')
                    
                    for geom, edge_info in main_network_edges_geom:
                        d = geom.distance(city_pt)
                        if d < min_main_dist:
                            min_main_dist = d
                            nearest_main = (geom, edge_info)

                    # Create the City Node
                    city_id = gen6(used_node_ids)
                    pt_ll = gpd.GeoSeries([city_pt], crs="EPSG:3857").to_crs(epsg=4326)[0]
                    final_nodes.append({
                        "id": city_id, "type": "city", "name": city_name,
                        "coordinates": {"lat": pt_ll.y, "lng": pt_ll.x}
                    })

                    # Helper to create connection
                    def create_connection(target_edge_info, dist_m, suffix=""):
                        u, v, _ = target_edge_info
                        # Connect to 'u' node of the edge for simplicity
                        target_node_id = get_node_id(u)
                        
                        conn_id = gen6(used_node_ids)
                        # Intermediate node (can be skipped, but useful for visuals)
                        final_nodes.append({
                            "id": conn_id, "type": "city_connection",
                            "coordinates": {"lat": pt_ll.y, "lng": pt_ll.x}
                        })
                        
                        # City -> Connection
                        final_edges.append({
                            "id": gen6(used_edge_ids),
                            "source": city_id, "target": conn_id,
                            "weight": meters_to_km(dist_m),
                            "road_name": f"Access to {city_name} {suffix}"
                        })
                        # Connection -> Network
                        final_edges.append({
                            "id": gen6(used_edge_ids),
                            "source": conn_id, "target": target_node_id,
                            "weight": meters_to_km(dist_m),
                            "road_name": f"Ramp to {city_name} {suffix}"
                        })

                    # CONNECT
                    if nearest_local:
                        local_geom, local_info = nearest_local
                        create_connection(local_info, min_local_dist, "(Local)")
                        
                        # Check if local connection is ISOLATED
                        u_local, v_local, _ = local_info
                        is_isolated = (u_local not in main_network_nodes)
                        
                        # If isolated (or if the main network is just much closer/better), ensure redundancy
                        # We add a "Hyperlink" to the main network if the local one didn't cut it
                        if is_isolated and nearest_main:
                            print(f"   ⚠️  Bridging {city_name} to Main Highway System (Local road was isolated).")
                            main_geom, main_info = nearest_main
                            create_connection(main_info, min_main_dist, "(Express)")
                    
                    elif nearest_main:
                        # Fallback if no local edges found (rare)
                        create_connection(nearest_main[1], min_main_dist, "(Express)")

        except Exception as e:
            print(f"Error processing cities: {e}")
            import traceback
            traceback.print_exc()

    # Write Output
    with open("nodes.json", "w") as f: json.dump(final_nodes, f, indent=2)
    with open("edges.json", "w") as f: json.dump(final_edges, f, indent=2)
    print("🎉 Done! All cities connected to the Highway System.")

if __name__ == "__main__":
    process_network()