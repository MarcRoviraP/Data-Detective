import requests
import json
import time

API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0cmViYWxsc3JvdmlyZXRhQGdtYWlsLmNvbSIsImp0aSI6ImJiZjNlYTc4LTk5MTMtNDI0Yi1hOGM4LTJiYzczMzVhZTg1OSIsImlzcyI6IkFFTUVUIiwiaWF0IjoxNzY5Njg1ODIxLCJ1c2VySWQiOiJiYmYzZWE3OC05OTEzLTQyNGItYThjOC0yYmM3MzM1YWU4NTkiLCJyb2xlIjoiIn0.BQPzQtgpZfivV1QPcZ8Srp5cle9l01TJ_nRzzQJv4m4"


def get_aemet_data(endpoint):
    url = f"https://opendata.aemet.es/opendata{endpoint}"
    headers = {
        'api_key': API_KEY,
        'cache-control': "no-cache"
    }

    print(f"Calling: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

    res_json = response.json()
    if res_json.get('estado') != 200:
        print(f"API Error: {res_json.get('estado')
                            } - {res_json.get('descripcion')}")
        return None

    data_url = res_json.get('datos')
    if not data_url:
        print("No data URL in response")
        return None

    print(f"Fetching actual data from: {data_url}")
    data_response = requests.get(data_url)
    return data_response.json()


def main():
    # 1. Test inventory to find a station ID
    print("Fetching station inventory...")
    # endpoint = "/api/valores/climatologicos/inventarioestaciones/todasestaciones"
    # To be more specific and faster, let's try a known station ID or just fetch all
    # For testing, let's try to get monthly data for a known Valencia station: 8414A (Valencia)

    # Endpoint for monthly climatology:
    # /api/valores/climatologicos/mensualesanuales/datos/anioini/{anioIniStr}/aniofin/{anioFinStr}/estacion/{idema}
    station_id = "8414A"  # Valencia
    year_start = "2023"
    year_end = "2024"
    endpoint = f"/api/valores/climatologicos/mensualesanuales/datos/anioini/{
        year_start}/aniofin/{year_end}/estacion/{station_id}"

    data = get_aemet_data(endpoint)
    if data:
        print("Successfully fetched data!")
        # Print first few records
        print(json.dumps(data[:2], indent=2))

        # Save to a temporary file for inspection
        with open("aemet_test_output.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Data saved to aemet_test_output.json")
    else:
        print("Failed to fetch data.")


if __name__ == "__main__":
    main()
