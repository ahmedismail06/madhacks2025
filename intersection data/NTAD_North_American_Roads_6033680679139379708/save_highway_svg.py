import geopandas as gpd
from shapely.geometry import MultiLineString

# --- CONFIGURATION ---
SHAPEFILE = "North_American_Roads.shp"
OUTPUT_SVG = "highways_lite.svg"

# 0.05 is aggressive. If lines look too blocky, try 0.03 (but file size will go up).
SIMPLIFY_TOLERANCE = 0.05 

# Decimal places for coordinates. 2 decimal places = ~1.1km precision.
# This is perfect for a full US map and saves massive space.
PRECISION = 2 

print("1. Loading & Filtering...")
# Load US Mainland bounding box only
bbox = (-126, 24, -66, 50)
gdf = gpd.read_file(SHAPEFILE, bbox=bbox)

# Filter for Class 1 Highways
if 'CLASS' in gdf.columns:
    gdf = gdf[gdf['CLASS'].astype(str) == '1']

print(f"   Original segments: {len(gdf)}")

print("2. Optimizing Geometry...")
# Simplify the shapes
gdf['geometry'] = gdf.geometry.simplify(tolerance=SIMPLIFY_TOLERANCE, preserve_topology=True)

# Calculate bounds for the SVG viewBox
minx, miny, maxx, maxy = gdf.total_bounds
width = maxx - minx
height = maxy - miny

print("3. Writing Raw SVG...")

with open(OUTPUT_SVG, 'w') as f:
    # Write Header
    # We flip the Y axis (miny - height) logic because SVGs count Y downwards, 
    # but map coordinates count Y upwards.
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx:.2f} {miny:.2f} {width:.2f} {height:.2f}">\n')
    
    # Styling group: all roads are black, 0.05 width
    # vector-effect="non-scaling-stroke" keeps lines thin even if you zoom in via CSS
    f.write('<g stroke="black" stroke-width="0.05" fill="none" vector-effect="non-scaling-stroke">\n')

    # Iterate through every road segment
    for geom in gdf.geometry:
        if geom.is_empty:
            continue
            
        # Handle MultiLineStrings (roads that are broken into pieces)
        parts = geom.geoms if isinstance(geom, MultiLineString) else [geom]
        
        for part in parts:
            # Extract coordinates
            coords = list(part.coords)
            if not coords: continue
            
            # Construct the Path Data (d attribute)
            # M = Move to start, L = Draw Line to next
            # We round every number to {PRECISION} decimal places
            path_data = ["M"]
            
            # Start point
            start_x, start_y = coords[0]
            # Flip Y for standard SVG rendering if needed, but since we set the ViewBox 
            # to match the lat/lon coordinates, we can usually just write them raw 
            # and flip the whole SVG with CSS "transform: scale(1, -1)" if it looks upside down.
            # For simplicity here, we write raw Lat/Lon.
            
            path_data.append(f"{start_x:.{PRECISION}f} {start_y:.{PRECISION}f}")
            
            # Remaining points
            for x, y in coords[1:]:
                path_data.append(f"L {x:.{PRECISION}f} {y:.{PRECISION}f}")
            
            # Join and write
            f.write(f'  <path d="{" ".join(path_data)}" />\n')

    f.write('</g>\n</svg>')

print(f"Done! Saved to {OUTPUT_SVG}")
print("Note: If the map looks upside down in your browser, add 'transform: scaleY(-1)' to the SVG style.")