import json

# CONFIGURATION
NODES_FILE = 'nodes.json'
EDGES_FILE = 'edges.json'
OUTPUT_FILE = 'network.geojson'
DECIMAL_PRECISION = 5  # 5 decimals = ~1 meter precision (Small file size)

def main():
    print(f"Loading data from {NODES_FILE} and {EDGES_FILE}...")
    try:
        with open(NODES_FILE, 'r') as f:
            nodes_data = json.load(f)
        with open(EDGES_FILE, 'r') as f:
            edges_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    node_lookup = {}
    
    # 1. Build Node Lookup (Rounded for small size)
    for node in nodes_data:
        lng = round(node['coordinates']['lng'], DECIMAL_PRECISION)
        lat = round(node['coordinates']['lat'], DECIMAL_PRECISION)
        node_lookup[node['id']] = [lng, lat]

    features = []
    
    # 2. Extract Segments for Leaflet
    print("Extracting coordinates...")
    for edge in edges_data:
        p1 = None
        p2 = None
        
        # Option A: From Geometry (First & Last only - Straight Line)
        if 'geometry' in edge and edge['geometry']:
            raw_geom = edge['geometry']
            p1 = [raw_geom[0][1], raw_geom[0][0]] # Swap Lat/Lng -> Lng/Lat
            p2 = [raw_geom[-1][1], raw_geom[-1][0]]
            
        # Option B: From Node IDs
        else:
            u = edge['source']
            v = edge['target']
            if u in node_lookup and v in node_lookup:
                p1 = node_lookup[u]
                p2 = node_lookup[v]
        
        if p1 and p2:
            # Filter Lat < 24.0 (Puerto Rico/Artifacts)
            if p1[1] < 24.0 or p2[1] < 24.0:
                continue
            
            # Ensure rounding
            p1 = [round(x, DECIMAL_PRECISION) for x in p1]
            p2 = [round(x, DECIMAL_PRECISION) for x in p2]
            
            # Create Feature
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [p1, p2]
                },
                "properties": {} # Empty properties for smallest file size
            }
            features.append(feature)

    # 3. Construct FeatureCollection (Leaflet Standard)
    geojson_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    # 4. Save
    print(f"Writing {len(features)} lines to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        # separators removes whitespace to make it load faster in Leaflet
        json.dump(geojson_collection, f, separators=(',', ':'))
    
    print(f"✅ Done! Generated '{OUTPUT_FILE}' ready for Leaflet.")

if __name__ == "__main__":
    main()