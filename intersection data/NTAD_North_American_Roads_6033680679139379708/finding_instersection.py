import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# --- CONFIGURATION ---
# Replace this with the exact name of your downloaded .shp file
INPUT_SHAPEFILE = "North_American_Roads.shp"
OUTPUT_CSV = "highway_intersections.csv"

print("1. Loading Shapefile... (This may take a moment)")
gdf = gpd.read_file(INPUT_SHAPEFILE)

# --- FILTERING ---
# The map you shared used "CLASS" = 1.
# We filter to ensure we are only looking at those major highways.
print("2. Filtering for Class 1 (Highways)...")
if 'CLASS' in gdf.columns:
    # Ensure we match numeric or string types
    highway_gdf = gdf[gdf['CLASS'].astype(str) == '1'].copy()
else:
    print("Warning: 'CLASS' column not found. Using dataset as is.")
    highway_gdf = gdf.copy()

print(f"   Found {len(highway_gdf)} highway segments.")

# --- EXTRACTING NODES ---
print("3. Identifying connection points...")

# We extract the start and end points of every line segment.
# In GIS topology, intersections are where these endpoints meet.
endpoints = []

for geom in highway_gdf.geometry:
    if geom.geom_type == 'LineString':
        # Extract first and last coordinate
        coords = list(geom.coords)
        endpoints.append(coords[0]) # Start point
        endpoints.append(coords[-1]) # End point
    elif geom.geom_type == 'MultiLineString':
        for part in geom.geoms:
            coords = list(part.coords)
            endpoints.append(coords[0])
            endpoints.append(coords[-1])

# --- FINDING INTERSECTIONS ---
print("4. Calculating intersections...")

# Create a DataFrame of all points
points_df = pd.DataFrame(endpoints, columns=['lon', 'lat'])

# Count how many times each coordinate appears.
# If a point appears 3 or more times, it's a junction (T-intersection or 4-way).
# If it appears 2 times, it's typically just two road segments connecting (a straight line).
point_counts = points_df.groupby(['lat', 'lon']).size().reset_index(name='degree')

# Filter for actual intersections (Degree >= 3 is a safe bet for junctions)
# Change to >= 2 if you want EVERY connection, even just road continuations.
intersections = point_counts[point_counts['degree'] >= 3]

print(f"   Found {len(intersections)} major intersections.")

# --- EXPORTING ---
print(f"5. Saving to {OUTPUT_CSV}...")
intersections.to_csv(OUTPUT_CSV, index=False)

print("Done! Open the CSV to see your coordinates.")