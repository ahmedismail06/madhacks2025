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

    # --- LOAD AND ADD CITIES ---
    cities_added = 0
    if os.path.exists(CITIES_CSV):
        try:
            print(f"5. Loading cities from {CITIES_CSV}...")
            df_cities = pd.read_csv(CITIES_CSV)
            
            print(f"   Columns found: {list(df_cities.columns)}")

            # Find lon/lat columns
            lon_col = None
            lat_col = None
            name_col = None
            for c in ['lng', 'lon', 'longitude', 'Longitude', 'LONGITUDE', 'long', 'x', 'X']:
                if c in df_cities.columns:
                    lon_col = c
                    break
            for c in ['lat', 'Lat', 'latitude', 'Latitude', 'LATITUDE', 'y', 'Y']:
                if c in df_cities.columns:
                    lat_col = c
                    break
            for c in ['city', 'name', 'City', 'Name', 'CITY', 'NAME']:
                if c in df_cities.columns:
                    name_col = c
                    break

            if lon_col and lat_col:
                print(f"   Using columns: name={name_col}, lat={lat_col}, lon={lon_col}")
                # Create GeoDataFrame from cities
                try:
                    # Convert to numeric first, handling any parsing issues
                    lats = pd.to_numeric(df_cities[lat_col], errors='coerce')
                    lons = pd.to_numeric(df_cities[lon_col], errors='coerce')

                    # Drop rows with invalid coordinates
                    valid_mask = lats.notna() & lons.notna()
                    df_cities_clean = df_cities[valid_mask].copy()
                    lats = lats[valid_mask]
                    lons = lons[valid_mask]

                    # --- FILTER: only USA and population > 500k ---
                    # detect country column
                    country_col = None
                    for c in ['country','country_code','countrycode','iso2','iso','country_name','country_name_en','ctry','nation']:
                        if c in df_cities_clean.columns:
                            country_col = c
                            break

                    is_us = None
                    if country_col is not None:
                        countries = df_cities_clean[country_col].astype(str).str.upper()
                        is_us = countries.isin(['US','USA','UNITED STATES','UNITED STATES OF AMERICA'])
                    else:
                        # if no country column but state-like column exists, assume US
                        for s in ['state','state_id','state_code','state_name']:
                            if s in df_cities_clean.columns:
                                is_us = pd.Series([True] * len(df_cities_clean), index=df_cities_clean.index)
                                break

                    if is_us is None:
                        # no clear US indicator, drop all (user requested USA only)
                        df_cities_clean = df_cities_clean.iloc[0:0]
                    else:
                        df_cities_clean = df_cities_clean[is_us].copy()

                    # detect population column
                    pop_col = None
                    for c in ['population','pop','population_total','pop_total','population_est','population2020','population_2020']:
                        if c in df_cities_clean.columns:
                            pop_col = c
                            break

                    if pop_col is not None:
                        pops = pd.to_numeric(df_cities_clean[pop_col], errors='coerce')
                        df_cities_clean = df_cities_clean[pops > 500000].copy()
                    else:
                        # no population info - filter out (require population)
                        df_cities_clean = df_cities_clean.iloc[0:0]

                    city_pts = [Point(lon, lat) for lon, lat in zip(df_cities_clean[lon_col].astype(float), df_cities_clean[lat_col].astype(float))]
                    cities_gdf = gpd.GeoDataFrame(df_cities_clean, geometry=city_pts, crs='EPSG:4326')
                    cities_gdf = cities_gdf.to_crs(epsg=3857)
                    print(f"   Created {len(cities_gdf)} valid city points (USA, population>500k)")
                except Exception as e:
                    print(f"   Error creating city points: {e}")
                    import traceback
                    traceback.print_exc()
                    cities_gdf = None

                if cities_gdf is None or len(cities_gdf) == 0:
                    print("   ⚠️  No cities loaded.")
                else:
                    for idx, city_row in cities_gdf.iterrows():
                        # geometry in cities_gdf is already in EPSG:3857
                        city_pt = city_row.geometry
                        city_name = city_row[name_col] if name_col else f"City_{idx}"

                        # Find nearest edge and point on that edge
                        min_edge_dist = float('inf')
                        nearest_edge = None
                        nearest_point_on_edge = None

                        for u, v, data_edge in G.edges(data=True):
                            edge_geom = data_edge.get('geometry')
                            if edge_geom is None:
                                continue
                            try:
                                closest_pt = edge_geom.interpolate(edge_geom.project(city_pt))
                                dist = city_pt.distance(closest_pt)
                            except Exception:
                                continue

                            if dist < min_edge_dist:
                                min_edge_dist = dist
                                nearest_edge = (u, v, data_edge)
                                nearest_point_on_edge = closest_pt

                        if nearest_edge is not None and nearest_point_on_edge is not None:
                            u, v, edge_data = nearest_edge

                            # Create city node
                            city_key = f"city_{idx}"
                            city_node_id = gen6(used_node_ids)

                            pt_latlon = gpd.GeoSeries([nearest_point_on_edge], crs="EPSG:3857").to_crs(epsg=4326)[0]

                            city_node = {
                                "id": city_node_id,
                                "type": "city",
                                "name": city_name,
                                "coordinates": {
                                    "lat": pt_latlon.y,
                                    "lng": pt_latlon.x
                                },
                                "source": CITIES_CSV
                            }
                            final_nodes.append(city_node)
                            node_id_map[city_key] = city_node_id

                            # Create edge from city to nearest point on road
                            distance_to_road_km = meters_to_km(min_edge_dist)

                            # Create intermediate connection node on the road (at nearest_point_on_edge)
                            connection_key = f"city_connection_{idx}"
                            connection_node_id = gen6(used_node_ids)

                            connection_node = {
                                "id": connection_node_id,
                                "type": "city_connection",
                                "coordinates": {
                                    "lat": pt_latlon.y,
                                    "lng": pt_latlon.x
                                }
                            }
                            final_nodes.append(connection_node)

                            # Edge from city to connection
                            final_edges.append({
                                "id": gen6(used_edge_ids),
                                "source": city_node_id,
                                "target": connection_node_id,
                                "weight": distance_to_road_km,
                                "road_name": f"Access to {city_name}",
                                "traffic_load": rand(0.0, 1.0),
                                "base_ms": rand(0.001, 0.005),
                                "risk": rand(0.02, 0.07),
                                "degrade_rate": rand(0.02, 0.05)
                            })

                            # Connect connection node to nearest graph node (use u)
                            nearest_node_u = get_node_id(u)
                            final_edges.append({
                                "id": gen6(used_edge_ids),
                                "source": connection_node_id,
                                "target": nearest_node_u,
                                "weight": distance_to_road_km,
                                "road_name": f"Road connection to {city_name}",
                                "traffic_load": rand(0.0, 1.0),
                                "base_ms": rand(0.001, 0.005),
                                "risk": rand(0.02, 0.07),
                                "degrade_rate": rand(0.02, 0.05)
                            })

                            cities_added += 1

                print(f"   ✅ Added {cities_added} cities to the network.")
            else:
                print(f"   ⚠️  Could not find required columns. Found: {list(df_cities.columns)}")

        except Exception as e:
            print(f"   ❌ Error reading cities CSV: {e}")
    else:
        print(f"   ⚠️  Cities CSV '{CITIES_CSV}' not found; continuing without cities.")

    with open("nodes.json", "w") as f:
        json.dump(final_nodes, f, indent=2)

    with open("edges.json", "w") as f:
        json.dump(final_edges, f, indent=2)

    print("🎉 Done! Data is processed. You can now run visualize_map.py")

if __name__ == "__main__":
    process_network()