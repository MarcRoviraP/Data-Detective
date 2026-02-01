import requests
import json
import time
from typing import List, Optional, Dict


class AEMETDataService:
    BASE_URL = "https://opendata.aemet.es/opendata"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'api_key': self.api_key,
            'cache-control': "no-cache"
        }

    def _get_data_from_endpoint(self, endpoint: str) -> Optional[List[Dict]]:
        """
        Generic method to call AEMET endpoints and fetch the final JSON data.
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()

            res_json = response.json()
            if res_json.get('estado') != 200:
                print(f"API Error ({res_json.get('estado')}): {
                      res_json.get('descripcion')}")
                return None

            data_url = res_json.get('datos')
            if not data_url:
                print("No data URL in response")
                return None

            # Second call to get the actual data
            data_response = requests.get(data_url, timeout=15)
            data_response.raise_for_status()
            return data_response.json()

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def fetch_monthly_data(self, station_id: str, year_start: str, year_end: str) -> Optional[List[Dict]]:
        """
        Fetches monthly climatological data for a station between two years.
        Handles the 36-month limitation by splitting requests if necessary.
        """
        start = int(year_start)
        end = int(year_end)

        all_data = []

        # We'll fetch in chunks of 3 years (36 months)
        for chunk_start in range(start, end + 1, 3):
            chunk_end = min(chunk_start + 2, end)
            print(f"  Fetching chunk: {chunk_start} to {chunk_end}...")

            endpoint = f"/api/valores/climatologicos/mensualesanuales/datos/anioini/{
                chunk_start}/aniofin/{chunk_end}/estacion/{station_id}"
            chunk_data = self._get_data_from_endpoint(endpoint)

            if chunk_data:
                all_data.extend(chunk_data)
            else:
                print(f"  Warning: Failed to fetch chunk {
                      chunk_start}-{chunk_end}")

            # Brief sleep to avoid rate limiting
            time.sleep(1)

        return all_data if all_data else None

    def fetch_stations_inventory(self) -> Optional[List[Dict]]:
        """
        Fetches the complete inventory of meteorological stations.
        """
        endpoint = "/api/valores/climatologicos/inventarioestaciones/todasestaciones"
        return self._get_data_from_endpoint(endpoint)

    def fetch_station_info(self, station_id: str) -> Optional[Dict]:
        """
        Helper to find info for a specific station from the inventory.
        """
        inventory = self.fetch_stations_inventory()
        if not inventory:
            return None

        for station in inventory:
            if station.get('indicativo') == station_id:
                return station
        return None
