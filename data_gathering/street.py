import requests
import zipfile
import io
import os

def download_tiger_roads():
    # 1. CONFIGURATION
    # The US Census Bureau released the 2025 TIGER/Line Shapefiles in September 2025.
    # We are fetching the "Primary Roads" (Interstates/Highways) for the entire nation.
    DATA_URL = "https://www2.census.gov/geo/tiger/TIGER2025/PRIMARYROADS/tl_2025_us_primaryroads.zip"
    SAVE_FOLDER = "us_interstate_data"

    # Create folder
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    print(f"--- Starting Download from US Census Bureau (2025 Data) ---")
    print(f"URL: {DATA_URL}")

    try:
        # 2. DOWNLOAD (Stream large file)
        response = requests.get(DATA_URL, stream=True)

        # Check if the file actually exists (catch 404s if 2025 directory structure changed)
        if response.status_code != 200:
            print(f"❌ Failed to download. Status Code: {response.status_code}")
            print("The 2025 file might not be indexed yet. Try switching URL to TIGER2024.")
            return

        total_size = int(response.headers.get('content-length', 0))

        # Download into memory
        print("Downloading... (approx 100MB)")
        z = zipfile.ZipFile(io.BytesIO(response.content))

        # 3. EXTRACT
        print(f"Extracting to {SAVE_FOLDER}...")
        z.extractall(SAVE_FOLDER)

        print(f"🎉 Success! Data saved in folder: '{SAVE_FOLDER}'")
        print(f"Look for the file: tl_2025_us_primaryroads.shp")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    download_tiger_roads()