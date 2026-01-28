import requests
import os

PACKAGE_SEARCH_URL = f"https://dadesobertes.gva.es/api/3/action/package_search"


def download_url(ano: int, mes: int) -> str:
    
    url = f"{PACKAGE_SEARCH_URL}?q=title:contaminantes+title:atmosf%C3%A9ricos+title:ozono+AND+title:{ano}&rows=100"
    response = requests.get(url, timeout=15)
    data = response.json()
    if not data.get("success"):
        raise RuntimeError("La API CKAN no devolvió success=true")
    return data["result"]["results"][0]["resources"][mes-1]["url"] if data["result"]["results"] else ""

def download_csv(url: str, output_filename: str) -> None:
    """
    Descarga el CSV desde la URL.
    """
    response = requests.get(url)
    response.raise_for_status()

    output_path = os.path.join("csv_contaminacion", output_filename)
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"✔ Archivo descargado: {output_path}")

def main():
    if not os.path.exists("csv_contaminacion"):
        os.makedirs("csv_contaminacion")
        
    year = int(input("Ingrese el año (YYYY): "))
    month = int(input("Ingrese el mes (MM): "))
    
    try:
        url = download_url(year,month)
        print(f"URL de descarga: {url}")

        download_csv(url, f"contaminacion_{year}_{month:02d}.csv")
    except Exception as e:
        print(f"Sin resultados para el año {year} y mes {month:02d}.")
if __name__ == "__main__":
    main()