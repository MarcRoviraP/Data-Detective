from AEMETDataService import AEMETDataService
import json

API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0cmViYWxsc3JvdmlyZXRhQGdtYWlsLmNvbSIsImp0aSI6ImJiZjNlYTc4LTk5MTMtNDI0Yi1hOGM4LTJiYzczMzVhZTg1OSIsImlzcyI6IkFFTUVUIiwiaWF0IjoxNzY5Njg1ODIxLCJ1c2VySWQiOiJiYmYzZWE3OC05OTEzLTQyNGItYThjOC0yYmM3MzM1YWU4NTkiLCJyb2xlIjoiIn0.BQPzQtgpZfivV1QPcZ8Srp5cle9l01TJ_nRzzQJv4m4"


def main():
    service = AEMETDataService(API_KEY)
    print("Fetching all stations...")
    stations = service.fetch_stations_inventory()

    if stations:
        # Filter by province "VALENCIA"
        valencia_stations = [
            s for s in stations if s.get('provincia') == 'VALENCIA']
        print(f"Found {len(valencia_stations)} stations in VALENCIA province.")

        # Save to a file for reference
        with open("valencia_stations.json", "w", encoding="utf-8") as f:
            json.dump(valencia_stations, f, indent=2, ensure_ascii=False)

        for s in valencia_stations:
            print(f"- {s.get('indicativo')}: {s.get('nombre')
                                              } ({s.get('latitud')}, {s.get('longitud')})")
    else:
        print("Failed to fetch stations.")


if __name__ == "__main__":
    main()
