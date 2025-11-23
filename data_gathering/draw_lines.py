import geopandas as gpd
import matplotlib.pyplot as plt
import os
import json
import pandas as pd
from shapely.geometry import Point, Polygon, box, LineString, MultiLineString

# CONFIGURATION
CLEAN_FILE_PATH = "cleaned_network.gpkg"
RAW_FILE_PATH = "us_interstate_data/tl_2025_us_primaryroads.shp"
INTERSECTIONS_CSV = "cleaned_intersections.csv"
NODES_JSON = "nodes.json"

def draw_map():
    # 1. Load the data
    if os.path.exists(CLEAN_FILE_PATH):
        print(f"Loading CLEAN map data from {CLEAN_FILE_PATH}...")
        gdf = gpd.read_file(CLEAN_FILE_PATH)
    else:
        print("⚠️ Clean file not found. Falling back to RAW data.")
        try:
            gdf = gpd.read_file(RAW_FILE_PATH)
        except Exception as e:
            print(f"❌ Error loading raw file: {e}")
            return

    # --- STEP 1: Project to EPSG:5070 (Meters) ---
    # This flattens the map accurately for the US
    print("Projecting to EPSG:5070 (Meters)...")
    gdf = gdf.to_crs(epsg=5070)

    # --- NEW: Convert each geometry to a straight line using its
    # first and last coordinate. This produces straight (chord) lines
    # instead of following the original polyline.
    def _to_straight(geom):
        if geom is None:
            return geom
        try:
            gt = geom.geom_type
        except Exception:
            return geom

        # LineString: take first and last coordinate
        if gt == 'LineString':
            coords = list(geom.coords)
            if len(coords) >= 2:
                return LineString([coords[0], coords[-1]])
            return geom

        # MultiLineString: use first coord of first part and last coord of last part
        if gt == 'MultiLineString':
            parts = list(geom.geoms)
            if len(parts) >= 1:
                try:
                    first = list(parts[0].coords)[0]
                    last = list(parts[-1].coords)[-1]
                    return LineString([first, last])
                except Exception:
                    return geom
            return geom

        # Fallback: try to extract coords attribute and build a straight line
        try:
            coords = list(geom.coords)
            if len(coords) >= 2:
                return LineString([coords[0], coords[-1]])
        except Exception:
            pass

        return geom

    print("Converting road geometries to straight start-end lines...")
    gdf['geometry'] = gdf.geometry.apply(_to_straight)

    # --- STEP 2: Convert Meters to Kilometers ---
    print("Scaling coordinates to Kilometers...")
    # We scale relative to (0,0) to keep the map structure intact
    gdf['geometry'] = gdf.geometry.scale(xfact=0.001, yfact=0.001, origin=(0,0))

    print(f"Loaded {len(gdf)} road segments.")
    print("Plotting...")

    fig, ax = plt.subplots(figsize=(20, 12))

    # Plot
    gdf.plot(ax=ax, color='#1f77b4', linewidth=0.8, alpha=0.8)

    # --- STEP 3: Load and plot intersections (if available) ---
    # Prefer `nodes.json` (produced by `street_clean.py`) when available
    if os.path.exists(NODES_JSON):
        print(f"Loading intersection nodes from {NODES_JSON}...")
        try:
            with open(NODES_JSON, 'r') as f:
                nodes = json.load(f)

            # Build a DataFrame of points from nodes.json (expecting lat/lng)
            rows = []
            for n in nodes:
                coord = n.get('coordinates') or {}
                lat = coord.get('lat')
                lng = coord.get('lng')
                if lat is None or lng is None:
                    continue
                rows.append({
                    'id': n.get('id'),
                    'type': n.get('type'),
                    'source': n.get('source'),
                    'lat': lat,
                    'lng': lng,
                    'name': n.get('name')
                })

            if rows:
                df_nodes = pd.DataFrame(rows)
                pts = [Point(xy) for xy in zip(df_nodes['lng'].astype(float), df_nodes['lat'].astype(float))]
                pts_gdf = gpd.GeoDataFrame(df_nodes, geometry=pts, crs='EPSG:4326')

                # Transform to map CRS and scale to KM
                pts_gdf = pts_gdf.to_crs(epsg=5070)
                pts_gdf['geometry'] = pts_gdf.geometry.scale(xfact=0.001, yfact=0.001, origin=(0,0))

                # --- NEW: Project regen spots onto nearest straight road geometry ---
                try:
                    # Prepare a copy of road geometries (already straightened and scaled above)
                    road_geoms = gdf.geometry.reset_index(drop=True)

                    regen_mask = pts_gdf['type'] == 'regen_spot'
                    projected_count = 0
                    if regen_mask.any():
                        for ridx, rrow in pts_gdf[regen_mask].iterrows():
                            pt = rrow.geometry
                            try:
                                # compute distances to all roads and pick the nearest
                                dists = road_geoms.distance(pt)
                                nearest_pos = dists.idxmin()
                                nearest_line = road_geoms.iloc[nearest_pos]
                                if nearest_line is None:
                                    continue
                                # place the regen point onto the nearest line (linear reference)
                                proj_pt = nearest_line.interpolate(nearest_line.project(pt))
                                pts_gdf.at[ridx, 'geometry'] = proj_pt
                                projected_count += 1
                            except Exception:
                                # on any error for a single point, skip it
                                continue
                    print(f"Projected {projected_count} regen spots onto nearest straight lines.")
                except Exception as e:
                    print(f"Warning: could not project regen spots onto lines: {e}")

                # Color by source/type
                csv_pts = pts_gdf[pts_gdf['source'] == INTERSECTIONS_CSV]
                regen_pts = pts_gdf[pts_gdf['type'] == 'regen_spot']
                city_pts = pts_gdf[pts_gdf['type'] == 'city']
                other_pts = pts_gdf[~pts_gdf.index.isin(csv_pts.index) & ~pts_gdf.index.isin(regen_pts.index) & ~pts_gdf.index.isin(city_pts.index)]

                # if len(other_pts):
                #     other_pts.plot(ax=ax, color='black', markersize=10, marker='x', label='Intersections')
                if len(regen_pts):
                    regen_pts.plot(ax=ax, color='orange', markersize=6, marker='o', label='Regen Spots')
                if len(csv_pts):
                    csv_pts.plot(ax=ax, color='red', markersize=18, marker='o', label='CSV Intersections')
                # Plot cities (large marker + label)
                if len(city_pts):
                    city_pts.plot(ax=ax, color='green', markersize=80, marker='*', label='Cities')
                    # add labels for cities
                    for _i, crow in city_pts.iterrows():
                        try:
                            x, y = crow.geometry.x, crow.geometry.y
                            name = crow.get('name') or ''
                            if name:
                                ax.text(x + 10, y + 10, name, fontsize=8, color='black', weight='bold')
                        except Exception:
                            continue

                # draw city-related access edges from edges.json if available
                try:
                    import os as _os
                    if _os.path.exists('edges.json'):
                        with open('edges.json', 'r') as ef:
                            edges = json.load(ef)

                        # build mapping id->geometry from pts_gdf
                        id_geom = {str(r['id']): g for r, g in zip(pts_gdf['id'], pts_gdf['geometry'])}
                        # identify city ids
                        city_ids = set([str(i) for i in city_pts['id']])

                        access_lines = []
                        for e in edges:
                            s = str(e.get('source'))
                            t = str(e.get('target'))
                            rn = e.get('road_name', '') or ''
                            # prefer edges that connect to city nodes or are access/connection edges
                            if (s in city_ids) or (t in city_ids) or ('Access to' in rn) or ('Road connection to' in rn):
                                if s in id_geom and t in id_geom:
                                    try:
                                        line = LineString([id_geom[s], id_geom[t]])
                                        access_lines.append(line)
                                    except Exception:
                                        continue

                        if access_lines:
                            acc_gdf = gpd.GeoDataFrame(geometry=access_lines, crs=pts_gdf.crs)
                            acc_gdf.plot(ax=ax, color='gray', linewidth=1.0, linestyle='--', alpha=0.8, label='City Access')
                except Exception:
                    pass

                ax.legend()
                print(f"Plotted {len(pts_gdf)} nodes from {NODES_JSON} (CSV: {len(csv_pts)})")
            else:
                print(f"No valid lat/lng entries found in {NODES_JSON}; falling back to CSV.")

        except Exception as e:
            print(f"Error loading {NODES_JSON}: {e}; falling back to CSV file.")
            # fall through to original CSV behavior

    # Fallback: if nodes.json not available or had issues, try the CSV directly
    if not os.path.exists(NODES_JSON):
        if os.path.exists(INTERSECTIONS_CSV):
            print(f"Loading intersections from {INTERSECTIONS_CSV} (fallback)...")
            try:
                df = pd.read_csv(INTERSECTIONS_CSV)
                lon_col = None
                lat_col = None
                for c in ['lon','lng','longitude','x','long','LONGITUDE','X']:
                    if c in df.columns:
                        lon_col = c
                        break
                for c in ['lat','latitude','y','LATITUDE','Y']:
                    if c in df.columns:
                        lat_col = c
                        break

                pts_gdf = None
                if lon_col and lat_col:
                    pts = [Point(xy) for xy in zip(df[lon_col].astype(float), df[lat_col].astype(float))]
                    pts_gdf = gpd.GeoDataFrame(df.copy(), geometry=pts, crs="EPSG:4326")
                elif 'geometry' in df.columns:
                    try:
                        from shapely import wkt
                        geom = df['geometry'].apply(lambda s: wkt.loads(s) if isinstance(s, str) else s)
                        pts_gdf = gpd.GeoDataFrame(df.copy(), geometry=geom, crs="EPSG:4326")
                    except Exception:
                        print("Could not parse 'geometry' column as WKT; skipping intersections plotting.")
                else:
                    print("No recognized coordinate columns in intersections CSV; skipping intersections plotting.")

                if pts_gdf is not None and len(pts_gdf):
                    pts_gdf = pts_gdf.to_crs(epsg=5070)
                    pts_gdf['geometry'] = pts_gdf.geometry.scale(xfact=0.001, yfact=0.001, origin=(0,0))
                    pts_gdf.plot(ax=ax, color='red', markersize=12, marker='o', label='Intersections')
                    ax.legend()
                    print(f"Plotted {len(pts_gdf)} intersections from CSV.")
                else:
                    print("No intersections to plot.")

            except Exception as e:
                print(f"Error loading intersections CSV: {e}")
        else:
            print(f"Intersections file '{INTERSECTIONS_CSV}' not found; skipping.")

    #ax.set_axis_off()
    plt.title("US Interstate System (Kilometers)", fontsize=24)

    # --- IMPORTANT: UPDATE LIMITS ---
    # Your old lat/lon limits (-126, 50, etc.) will make the map blank 
    # because the data is now in thousands of KMs.
    # I have commented them out to let Matplotlib auto-fit the US.
    
    ax.set_xlim([-2500, 2500]) # Example approx limits in KM for EPSG 5070
    ax.set_ylim([200, 3200])   # Example approx limits in KM for EPSG 5070

    print("Saving image to 'us_interstates_map_km.png'...")
    plt.savefig("us_interstates_map_km.png", dpi=300, bbox_inches='tight')

    
    # Note: avoid blocking interactive show so script finishes non-interactively.
    # If you want an interactive window, uncomment the following line.
    # plt.show()

def export_geojson(output_path="us_interstates_straight.geojson"):
    # 1. Load the data
    if os.path.exists(CLEAN_FILE_PATH):
        print(f"Loading CLEAN map data from {CLEAN_FILE_PATH}...")
        gdf = gpd.read_file(CLEAN_FILE_PATH)
    else:
        print("⚠️ Clean file not found. Falling back to RAW data.")
        gdf = gpd.read_file(RAW_FILE_PATH)

    # --- STEP 1: Project to EPSG:5070 (Meters) ---
    print("Projecting to EPSG:5070...")
    gdf = gdf.to_crs(epsg=5070)

    # --- STEP 2: Convert to straight-line chords ---
    def _to_straight(geom):
        if geom is None:
            return geom
        if geom.geom_type == "LineString":
            coords = list(geom.coords)
            if len(coords) >= 2:
                return LineString([coords[0], coords[-1]])
        if geom.geom_type == "MultiLineString":
            parts = list(geom.geoms)
            if len(parts) >= 1:
                first = list(parts[0].coords)[0]
                last = list(parts[-1].coords)[-1]
                return LineString([first, last])
        return geom

    print("Straightening geometries...")
    gdf["geometry"] = gdf.geometry.apply(_to_straight)

    # --- STEP 3: Scale to kilometers (still in projected CRS) ---
    print("Scaling coordinates to kilometers...")
    gdf["geometry"] = gdf.geometry.scale(xfact=0.001, yfact=0.001, origin=(0, 0))

    # --- STEP 4: Convert BACK to EPSG:4326 (lat/lon) ---
    print("Reprojecting to EPSG:4326...")
    gdf = gdf.to_crs(epsg=4326)

    # --- STEP 5: Export to GeoJSON ---
    print(f"Writing GeoJSON to {output_path}...")
    gdf.to_file(output_path, driver="GeoJSON")

    print("✅ Completed! GeoJSON is in EPSG:4326 (lat/lon).")


    

if __name__ == "__main__":
    # export_geojson()
    draw_map()
