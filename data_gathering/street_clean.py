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
INTERSECTIONS_CSV = "intersection data/NTAD_North_American_Roads_6033680679139379708/cleaned_intersections.csv"
CITIES_CSV = "uscities.csv"  # CSV with columns: name, lat, lon, population (optional)
SNAP_TOLERANCE_METERS = 500.0
MIN_COMPONENT_SIZE = 20

def process_network():
    def rand(a, b):
        return round(random.uniform(a, b), 6)

    print("1. Loading Shapefile...")
    if not os.path.exists(SHAPEFILE_PATH):
        print(f"❌ Error: Could not find {SHAPEFILE_PATH}")
        return

    gdf = gpd.read_file(SHAPEFILE_PATH)
    gdf = gdf.to_crs(epsg=3857)
    print(f"   Loaded {len(gdf)} road segments.")

    print("2. Converting to Graph...")
    G = momepy.gdf_to_nx(gdf, approach='primal')

    # --- BETTER CLEANING LOGIC ---
    print("2b. Cleaning Noise (Smart Filter)...")
    initial_node_count = len(G.nodes)

    # Find all connected groups (islands)
    components = list(nx.connected_components(G))
    print(f"    Found {len(components)} disconnected islands in the raw data.")

    # Keep ALL islands that are big enough to be real roads
    valid_nodes = []
    for component in components:
        if len(component) > MIN_COMPONENT_SIZE:
            valid_nodes.extend(component)

    G = G.subgraph(valid_nodes).copy()

    removed_count = initial_node_count - len(G.nodes)
    print(f"    ❌ Removed {removed_count} noise nodes (tiny artifacts).")
    print(f"    ✅ Keeping {len(G.nodes)} valid nodes (Real US Network).")

    # --- LOAD CLEANED INTERSECTIONS CSV AND SNAP TO GRAPH ---
    csv_points_3857 = []
    csv_unmatched = []
    csv_matches = {}
    if os.path.exists(INTERSECTIONS_CSV):
        try:
            print(f"Loading intersections from {INTERSECTIONS_CSV} and snapping to graph...")
            df_csv = pd.read_csv(INTERSECTIONS_CSV)

            # heuristics for lon/lat
            lon_col = None
            lat_col = None
            for c in ['lon','lng','longitude','x','long','LONGITUDE','X']:
                if c in df_csv.columns:
                    lon_col = c
                    break
            for c in ['lat','latitude','y','LATITUDE','Y']:
                if c in df_csv.columns:
                    lat_col = c
                    break

            pts_gdf = None
            if lon_col and lat_col:
                pts = [Point(xy) for xy in zip(df_csv[lon_col].astype(float), df_csv[lat_col].astype(float))]
                pts_gdf = gpd.GeoDataFrame(df_csv.copy(), geometry=pts, crs='EPSG:4326')
            elif 'geometry' in df_csv.columns:
                try:
                    from shapely import wkt
                    geom = df_csv['geometry'].apply(lambda s: wkt.loads(s) if isinstance(s, str) else s)
                    pts_gdf = gpd.GeoDataFrame(df_csv.copy(), geometry=geom, crs='EPSG:4326')
                except Exception:
                    print("Could not parse 'geometry' column in CSV; skipping CSV integration.")
            else:
                print("No lon/lat or geometry columns found in intersections CSV; skipping CSV integration.")

            if pts_gdf is not None and len(pts_gdf):
                pts_gdf = pts_gdf.to_crs(epsg=3857)
                for i, row in pts_gdf.iterrows():
                    pt = row.geometry
                    csv_points_3857.append((i, pt))

                node_items = list(G.nodes)
                node_points = {n: Point(n) if not hasattr(n, 'geom_type') else n for n in node_items}

                for i, pt in csv_points_3857:
                    min_node = None
                    min_dist = float('inf')
                    for n, np_pt in node_points.items():
                        try:
                            d = pt.distance(np_pt)
                        except Exception:
                            continue
                        if d < min_dist:
                            min_dist = d
                            min_node = n

                    if min_node is not None and min_dist <= SNAP_TOLERANCE_METERS:
                        csv_matches[i] = (min_node, min_dist)
                        try:
                            G.nodes[min_node]['csv_intersection'] = True
                            G.nodes[min_node].setdefault('csv_indices', []).append(i)
                        except Exception:
                            pass
                    else:
                        csv_unmatched.append((i, pt))

                print(f"  CSV intersections: {len(csv_points_3857)} loaded, {len(csv_matches)} snapped, {len(csv_unmatched)} unmatched.")

        except Exception as e:
            print(f"Error reading intersections CSV: {e}")
    else:
        print(f"Intersections CSV '{INTERSECTIONS_CSV}' not found; continuing without it.")

    # --- SAVE CLEANED MAP ---
    print(f"    💾 Saving cleaned map to {CLEAN_FILE_PATH}...")
    clean_gdf = momepy.nx_to_gdf(G, points=False, lines=True)
    clean_gdf.to_file(CLEAN_FILE_PATH, driver="GPKG")

    final_nodes = []
    final_edges = []

    def meters_to_km(m):
        return m / 1000.0
    
    def meters_to_miles(m):
        return m / 1609.344

    print("3. Processing Edges & Injecting Regen Spots...")

    used_node_ids = set()
    used_edge_ids = set()

    def gen6(used_set):
        new_id = f"{random.randint(0, 999999):06d}"
        while new_id in used_set:
            new_id = f"{random.randint(0, 999999):06d}"
        used_set.add(new_id)
        return new_id

    node_counter = 0
    node_id_map = {}

    def get_node_id(nx_node_key, is_regen=False, coords=None):
        nonlocal node_counter
        if nx_node_key not in node_id_map:
            node_id = gen6(used_node_ids)

            if coords is None:
                pt = Point(nx_node_key)
            else:
                pt = coords

            pt_latlon = gpd.GeoSeries([pt], crs="EPSG:3857").to_crs(epsg=4326)[0]

            is_routing = False
            try:
                if isinstance(nx_node_key, str) and nx_node_key.startswith('csv_'):
                    is_routing = True
                else:
                    if nx_node_key in G.nodes and G.nodes[nx_node_key].get('csv_intersection'):
                        is_routing = True
            except Exception:
                is_routing = False

            node_type = "regen_spot" if is_regen else ("routing_node" if is_routing else "network_node")

            node_data = {
                "id": node_id,
                "type": node_type,
                "coordinates": {
                    "lat": pt_latlon.y,
                    "lng": pt_latlon.x
                }
            }

            try:
                if isinstance(nx_node_key, str) and nx_node_key.startswith('csv_'):
                    node_data['source'] = INTERSECTIONS_CSV
                else:
                    if nx_node_key in G.nodes and G.nodes[nx_node_key].get('csv_intersection'):
                        node_data['source'] = INTERSECTIONS_CSV
            except Exception:
                pass

            final_nodes.append(node_data)
            node_id_map[nx_node_key] = node_id
            node_counter += 1

        return node_id_map[nx_node_key]

    # iterate edges and inject regen nodes when needed
    for u, v, data in G.edges(data=True):
        geom = data.get('geometry')
        if geom is None:
            continue

        length_miles = meters_to_miles(geom.length)

        if length_miles > REGEN_SPACING_MILES:
            num_segments = math.ceil(length_miles / REGEN_SPACING_MILES)
            segment_length = geom.length / num_segments

            current_start_node_id = get_node_id(u)
            end_node_id = get_node_id(v)

            for i in range(1, num_segments):
                dist_along = i * segment_length
                new_point = geom.interpolate(dist_along)

                regen_key = f"{u}_{v}_{i}"
                regen_node_id = get_node_id(regen_key, is_regen=True, coords=new_point)

                final_edges.append({
                    "id": gen6(used_edge_ids),
                    "source": current_start_node_id,
                    "target": regen_node_id,
                    "weight": meters_to_km(segment_length),
                    "road_name": data.get('FULLNAME', 'Unknown Road'),
                    "traffic_load": rand(0.0, 1.0),
                    "base_ms": rand(0.001, 0.005),
                    "risk": rand(0.02, 0.07),
                    "degrade_rate": rand(0.02, 0.05)
                })
                current_start_node_id = regen_node_id

            final_edges.append({
                "id": gen6(used_edge_ids),
                "source": current_start_node_id,
                "target": end_node_id,
                "weight": meters_to_km(segment_length),
                "road_name": data.get('FULLNAME', 'Unknown Road'),
                "traffic_load": rand(0.0, 1.0),
                "base_ms": rand(0.001, 0.005),
                "risk": rand(0.02, 0.07),
                "degrade_rate": rand(0.02, 0.05)
            })

        else:
            coords_latlon = [
                [p[1], p[0]] for p in
                gpd.GeoSeries([geom], crs="EPSG:3857").to_crs(epsg=4326)[0].coords
            ]

            final_edges.append({
                "id": gen6(used_edge_ids),
                "source": get_node_id(u),
                "target": get_node_id(v),
                "weight": meters_to_km(geom.length),
                "road_name": data.get('FULLNAME', 'Unknown Road'),
                "geometry": coords_latlon,
                "traffic_load": rand(0.0, 1.0),
                "base_ms": rand(0.001, 0.005),
                "risk": rand(0.02, 0.07),
                "degrade_rate": rand(0.02, 0.05)
            })

    print(f"4. Exporting {len(final_nodes)} nodes and {len(final_edges)} edges...")

    # --- ADD UNMATCHED CSV INTERSECTIONS TO NODES ---
    if 'csv_unmatched' in locals() and len(csv_unmatched):
        print(f"Adding {len(csv_unmatched)} unmatched CSV intersections to exported nodes...")
        for i, pt in csv_unmatched:
            key = f"csv_{i}"
            get_node_id(key, is_regen=False, coords=pt)

# ------------------------------------------------------------------
    # REPLACEMENT FOR STEP 5: CITY LOADING & BRIDGE LOGIC
    # ------------------------------------------------------------------

    # A. Identify the Main Network (Largest Connected Component)
    print("   ℹ️  Indexing Main Highway Network to prevent islands...")
    largest_cc = max(nx.connected_components(G), key=len)
    main_network_nodes = set(largest_cc)

    # B. Pre-filter "Main Network" edges for faster lookup
    main_network_edges = []
    for u, v, data in G.edges(data=True):
        if 'geometry' in data and u in main_network_nodes and v in main_network_nodes:
            main_network_edges.append((u, v, data))

    # C. Load Cities
    cities_added = 0
    if os.path.exists(CITIES_CSV):
        try:
            print(f"5. Loading cities from {CITIES_CSV}...")
            df_cities = pd.read_csv(CITIES_CSV)
            
            # --- Column Detection (Same as before) ---
            lon_col = next((c for c in df_cities.columns if c.lower() in ['lng','lon','longitude','x']), None)
            lat_col = next((c for c in df_cities.columns if c.lower() in ['lat','latitude','y']), None)
            name_col = next((c for c in df_cities.columns if c.lower() in ['city','name']), None)
            pop_col = next((c for c in df_cities.columns if c.lower() in ['population','pop']), None)

            # --- Filter & Create Geometry ---
            if lon_col and lat_col:
                # Filter for population > 500k if column exists
                if pop_col:
                    pops = pd.to_numeric(df_cities[pop_col], errors='coerce')
                    df_cities = df_cities[pops > 500000].copy()
                
                city_pts = [Point(xy) for xy in zip(df_cities[lon_col], df_cities[lat_col])]
                cities_gdf = gpd.GeoDataFrame(df_cities, geometry=city_pts, crs='EPSG:4326')
                cities_gdf = cities_gdf.to_crs(epsg=3857)
                print(f"   Processing {len(cities_gdf)} major cities...")

                for idx, city_row in cities_gdf.iterrows():
                    city_pt = city_row.geometry
                    city_name = city_row[name_col] if name_col else f"City_{idx}"

                    # 1. FIND NEAREST LOCAL EDGE (Any road, could be isolated)
                    min_local_dist = float('inf')
                    nearest_local = None
                    nearest_pt_local = None

                    for u, v, data in G.edges(data=True):
                        if 'geometry' not in data: continue
                        try:
                            # Project city point onto road line
                            proj = data['geometry'].project(city_pt)
                            pt_on_road = data['geometry'].interpolate(proj)
                            dist = city_pt.distance(pt_on_road)
                            if dist < min_local_dist:
                                min_local_dist = dist
                                nearest_local = (u, v, data)
                                nearest_pt_local = pt_on_road
                        except: continue

                    # 2. FIND NEAREST MAIN NETWORK EDGE (Guaranteed connected)
                    min_main_dist = float('inf')
                    nearest_main = None
                    nearest_pt_main = None

                    for u, v, data in main_network_edges:
                        try:
                            proj = data['geometry'].project(city_pt)
                            pt_on_road = data['geometry'].interpolate(proj)
                            dist = city_pt.distance(pt_on_road)
                            if dist < min_main_dist:
                                min_main_dist = dist
                                nearest_main = (u, v, data)
                                nearest_pt_main = pt_on_road
                        except: continue

                    # 3. CREATE CITY NODE
                    city_node_id = gen6(used_node_ids)
                    pt_latlon = gpd.GeoSeries([city_pt], crs="EPSG:3857").to_crs(epsg=4326)[0]
                    
                    final_nodes.append({
                        "id": city_node_id, "type": "city", "name": city_name,
                        "coordinates": {"lat": pt_latlon.y, "lng": pt_latlon.x},
                        "source": CITIES_CSV
                    })
                    cities_added += 1

                    # Helper to create edges
                    def add_connector(target_node_id, dist_meters, suffix):
                        conn_id = gen6(used_node_ids)
                        # Intermediate node
                        final_nodes.append({
                            "id": conn_id, "type": "city_connection",
                            "coordinates": {"lat": pt_latlon.y, "lng": pt_latlon.x}
                        })
                        # City -> Connection
                        final_edges.append({
                            "id": gen6(used_edge_ids), "source": city_node_id, "target": conn_id,
                            "weight": meters_to_km(dist_meters),
                            "road_name": f"Access to {city_name} {suffix}",
                            "traffic_load": rand(0.5, 0.9)
                        })
                        # Connection -> Network Node
                        final_edges.append({
                            "id": gen6(used_edge_ids), "source": conn_id, "target": target_node_id,
                            "weight": meters_to_km(dist_meters),
                            "road_name": f"Ramp to {city_name} {suffix}",
                            "traffic_load": rand(0.5, 0.9)
                        })

                    # 4. CONNECT TO LOCAL (Primary Connection)
                    is_isolated = True
                    if nearest_local:
                        u, v, _ = nearest_local
                        # Use 'u' as the anchor point on the graph
                        target_id = get_node_id(u) 
                        add_connector(target_id, min_local_dist, "(Local)")
                        
                        # Check if this local road is part of the main network
                        if u in main_network_nodes:
                            is_isolated = False

                    # 5. BRIDGE TO MAIN NETWORK (If isolated)
                    if is_isolated:
                        print(f"      ⚠️  {city_name} is on an island. Building bridge to Main Network...")
                        if nearest_main:
                            u_main, _, _ = nearest_main
                            target_id = get_node_id(u_main)
                            add_connector(target_id, min_main_dist, "(Express)")
                        else:
                            print(f"      ❌ CRITICAL: Could not find main network for {city_name}!")

            print(f"   ✅ Added {cities_added} cities (all connected to Main Network).")

        except Exception as e:
            print(f"   ❌ Error reading cities CSV: {e}")

    with open("nodes.json", "w") as f:
        json.dump(final_nodes, f, indent=2)

    with open("edges.json", "w") as f:
        json.dump(final_edges, f, indent=2)

    print("🎉 Done! Data is processed. You can now run visualize_map.py")

if __name__ == "__main__":
    process_network()