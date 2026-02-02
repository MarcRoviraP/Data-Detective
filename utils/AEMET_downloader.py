import os
import json
import time
from AEMETDataService import AEMETDataService

# API Key provided by the user
ts = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0cmViYWxsc3JvdmlyZXRhQGdtYWlsLmNvbSIsImp0aSI6ImJiZjNlYTc4LTk5MTMtNDI0Yi1hOGM4LTJiYzczMzVhZTg1OSIsImlzcyI6IkFFTUVUIiwiaWF0IjoxNzY5Njg1ODIxLCJ1c2VySWQiOiJiYmYzZWE3OC05OTEzLTQyNGItYThjOC0yYmM3MzM1YWU4NTkiLCJyb2xlIjoiIn0.BQPzQtgpZfivV1QPcZ8Srp5cle9l01TJ_nRzzQJv4m4"

# Configuration
YEAR_START = "2007"
YEAR_END = "2024"
OUTPUT_DIR = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), "data", "aemet_historical")
STATIONS_FILE = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), "utils", "valencia_stations.json")


def main():
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    # Load stations
    if not os.path.exists(STATIONS_FILE):
        print(
            f"Error: {STATIONS_FILE} not found. Run find_valencia_stations.py first.")
        return

    with open(STATIONS_FILE, "r", encoding="utf-8") as f:
        stations = json.load(f)

    service = AEMETDataService(ts)

    # Filter only city stations to avoid rate limits and focus on user interest
    city_station_ids = ["8414A", "8416", "8416X", "8416Y"]

    for station in stations:
        station_id = station['indicativo']
        if station_id not in city_station_ids:
            continue

        station_name = station['nombre']

        print(f"\n--- Fetching data for {station_name} ({station_id}) ---")
        data = service.fetch_monthly_data(station_id, YEAR_START, YEAR_END)

        if data:
            filename = f"monthly_{station_id}_{YEAR_START}_{YEAR_END}.json"
            filepath = os.path.join(OUTPUT_DIR, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Successfully downloaded {
                  len(data)} records for {station_id}.")
        else:
            print(f"Failed to fetch data for {station_id}.")

        # Rate limit safety
        time.sleep(5)

    print("\nAll downloads completed.")


if __name__ == "__main__":
    main()
