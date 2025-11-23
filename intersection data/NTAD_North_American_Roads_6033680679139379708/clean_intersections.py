import geopandas as gpd
import pandas as pd
import os

# --- CONFIGURATION ---
# 1. Your Intersection Points (The file with the red dots)
INPUT_CSV = "mainland_intersections.csv"

# 2. Your Grid/Lines (The file with the blue lines)
# Make sure this path is correct based on your folder structure!
ROADS_SHP = "us_interstate_data/tl_2025_us_primaryroads.shp"

# 3. The Output (The clean file)
OUTPUT_CSV = "cleaned_intersections.csv"

# 4. Tolerance (How far from the road is "too far"?)
# 0.02 degrees is approx 2.2 km.
TOLERANCE_DEG = 0.02

def clean_data():
    print(f"1. Loading Roads from {ROADS_SHP}...")
    if not os.path.exists(ROADS_SHP):
        print("❌ Error: Shapefile not found. Check the path.")
        return
        
    # Load roads and ensure they are in Lat/Lon (EPSG:4326)
    roads_gdf = gpd.read_file(ROADS_SHP).to_crs(epsg=4326)
    
    print(f"2. Loading Points from {INPUT_CSV}...")
    if not os.path.exists(INPUT_CSV):
        print("❌ Error: CSV file not found.")
        return

    df = pd.read_csv(INPUT_CSV)
    original_count = len(df)
    
    # Convert CSV to a GeoDataFrame (Spatial points)
    points_gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.lon, df.lat),
        crs="EPSG:4326"
    )

    print("3. creating 'Safe Zone' buffer around roads...")
    # This combines all roads into one big shape, padded by the tolerance
    road_buffer = roads_gdf.geometry.buffer(TOLERANCE_DEG).unary_union

    print("4. Filtering...")
    # Keep only points that are INSIDE that safe zone
    valid_points_mask = points_gdf.geometry.within(road_buffer)
    clean_gdf = points_gdf[valid_points_mask]
    
    # Calculate how many we deleted
    removed = original_count - len(clean_gdf)
    
    print(f"   Original: {original_count}")
    print(f"   Removed:  {removed} (Stray dots)")
    print(f"   Remaining: {len(clean_gdf)}")

    print(f"5. Saving to {OUTPUT_CSV}...")
    # Drop the geometry column before saving back to CSV
    clean_df = pd.DataFrame(clean_gdf.drop(columns='geometry'))
    clean_df.to_csv(OUTPUT_CSV, index=False)
    
    print("✅ Done! Use 'cleaned_intersections.csv' for your map now.")

if __name__ == "__main__":
    clean_data()