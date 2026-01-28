import requests
import datetime
from typing import List, Optional

class EstacionContaminacionAtmosferica:
    direccion, no2, pm10, o3, fecha_carg, calidad_am = "-", "-", "-", "-", "-", "-"
    geo_point_2d = None  # Coordenadas geográficas
    
    def imprimir_informacion(self):
        print(f"📍 {self.direccion}")
        print(f"🕒 {self.format_timestamp(self.fecha_carg)}")
        print(f"   - NO2 : {self.format_value(self.no2)} µg/m³")
        print(f"   - PM10: {self.format_value(self.pm10)} µg/m³")
        print(f"   - O3  : {self.format_value(self.o3)} µg/m³")
        print(f"   - Calidad: {self.calidad_am}")
        print("-" * 40)

    def format_timestamp(self, fecha) -> str:
        if not fecha:
            return "-"
        
        try:
            dt = datetime.datetime.fromisoformat(fecha)
            return dt.strftime("%d-%m-%Y %H:%M:%S")
        except (ValueError, TypeError):
            return fecha
        
    def format_value(self, value) -> str:
        return str(value) if value is not None else "-"

def get_air_quality_data() -> List[EstacionContaminacionAtmosferica]:
    """
    Obtiene datos de calidad del aire en tiempo real de Valencia OpenData.
    
    Returns:
        Lista de objetos EstacionContaminacionAtmosferica con datos de estaciones.
    """
    try:
        URL = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records?select=direccion%2Cno2%2Cpm10%2Co3%2Cfecha_carg%2Ccalidad_am%2Cgeo_point_2d&limit=20"

        response = requests.get(URL, timeout=15)
        response.raise_for_status()
        json_data = response.json().get("results", [])

        lista_estaciones = []

        for record in json_data:
            estacion = EstacionContaminacionAtmosferica()
            estacion.direccion = record.get("direccion", "-")
            estacion.no2 = record.get("no2", "-")
            estacion.pm10 = record.get("pm10", "-")
            estacion.o3 = record.get("o3", "-")
            estacion.fecha_carg = record.get("fecha_carg", "-")
            estacion.calidad_am = record.get("calidad_am", "-")
            estacion.geo_point_2d = record.get("geo_point_2d")  # {lat: X, lon: Y}

            lista_estaciones.append(estacion)

        return lista_estaciones
    
    except requests.RequestException as e:
        print(f"❌ Error al obtener datos de calidad del aire: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return []

def main():
    """Función principal para testing."""
    lista_estaciones = get_air_quality_data()
    
    if not lista_estaciones:
        print("No se pudieron obtener datos de calidad del aire.")
        return
    
    for estacion in lista_estaciones:
        estacion.imprimir_informacion()

if __name__ == "__main__":
    main()
