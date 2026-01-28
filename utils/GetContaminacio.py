import requests
import os
from typing import Optional

PACKAGE_SEARCH_URL = "https://dadesobertes.gva.es/api/3/action/package_search"


def get_download_url(ano: int, mes: int) -> Optional[str]:
    """
    Obtiene la URL de descarga para datos históricos de contaminación.
    
    Args:
        ano: Año (YYYY)
        mes: Mes (1-12)
    
    Returns:
        URL de descarga del CSV o None si no se encuentra.
    """
    try:
        url = f"{PACKAGE_SEARCH_URL}?q=title:contaminantes+title:atmosf%C3%A9ricos+title:ozono+AND+title:{ano}&rows=100"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        if not data.get("success"):
            print("⚠️ La API CKAN no devolvió success=true")
            return None
        
        results = data.get("result", {}).get("results", [])
        if not results:
            print(f"⚠️ No se encontraron datos para el año {ano}")
            return None
        
        resources = results[0].get("resources", [])
        if mes - 1 >= len(resources):
            print(f"⚠️ No hay datos para el mes {mes}")
            return None
        
        return resources[mes - 1].get("url", "")
    
    except requests.RequestException as e:
        print(f"❌ Error al obtener URL de descarga: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None


def download_csv(url: str, output_filename: str) -> bool:
    """
    Descarga el CSV desde la URL.
    
    Args:
        url: URL del CSV
        output_filename: Nombre del archivo de salida
    
    Returns:
        True si se descargó correctamente, False en caso contrario.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        output_path = os.path.join("csv_contaminacion", output_filename)
        os.makedirs("csv_contaminacion", exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"✔ Archivo descargado: {output_path}")
        return True
    
    except requests.RequestException as e:
        print(f"❌ Error al descargar CSV: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def get_historical_data(year: int, month: int) -> Optional[str]:
    """
    Obtiene datos históricos de contaminación para un año y mes específicos.
    
    Args:
        year: Año (YYYY)
        month: Mes (1-12)
    
    Returns:
        Ruta del archivo descargado o None si falla.
    """
    url = get_download_url(year, month)
    if not url:
        return None
    
    filename = f"contaminacion_{year}_{month:02d}.csv"
    if download_csv(url, filename):
        return os.path.join("csv_contaminacion", filename)
    
    return None


def main():
    """Función principal para testing."""
    if not os.path.exists("csv_contaminacion"):
        os.makedirs("csv_contaminacion")
        
    year = int(input("Ingrese el año (YYYY): "))
    month = int(input("Ingrese el mes (MM): "))
    
    filepath = get_historical_data(year, month)
    if filepath:
        print(f"✅ Datos históricos guardados en: {filepath}")
    else:
        print(f"❌ No se pudieron obtener datos para {year}-{month:02d}")


if __name__ == "__main__":
    main()
