import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
SHAPEFILE = "North_American_Roads.shp"
CSV_FILE = "highway_intersections.csv"

# Set a bounding box to zoom in? (Set to None to plot EVERYTHING)
# Example: Bounding box for US East Coast approx [-85, 24, -65, 45]
# Format: [min_lon, min_lat, max_lon, max_lat]
ZOOM_BOX = None 
# ZOOM_BOX = [-74.25, 40.5, -73.7, 40.9] # Example: Zoom into NYC area

print("1. Loading Data...")
roads = gpd.read_file(SHAPEFILE)
intersections = pd.read_csv(CSV_FILE)

# Filter roads just like before (Class 1)
if 'CLASS' in roads.columns:
    roads = roads[roads['CLASS'].astype(str) == '1']

print("2. Setting up the plot...")
fig, ax = plt.subplots(figsize=(15, 15)) # Big square image

# --- OPTIONAL: ZOOMING ---
if ZOOM_BOX:
    print(f"   Filtering data to {ZOOM_BOX}...")
    min_x, min_y, max_x, max_y = ZOOM_BOX
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)

print("3. Plotting Highways (Blue Lines)...")
# We plot roads first so they are at the back
roads.plot(ax=ax, color='blue', linewidth=0.5, alpha=0.6, label='Highways')

print("4. Plotting Intersections (Red Dots)...")
# We use standard matplotlib scatter for the CSV points
# s=1 makes the dots small enough to see without cluttering
ax.scatter(intersections['lon'], intersections['lat'], 
           color='red', s=2, label='Intersections', zorder=5)

# Labels and Styling
ax.set_title("North American Highway Intersections")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
plt.legend(loc='upper right')

print("5. Displaying...")
plt.show()