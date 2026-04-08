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
        # Nueva URL ArcGIS con outSR=4326 para obtener coordenadas en Lat/Lon
        URL = "https://geoportal.valencia.es/server/rest/services/OPENDATA/MedioAmbiente/MapServer/156/query?where=1=1&outFields=*&returnGeometry=true&f=pjson&outSR=4326"

        response = requests.get(URL, timeout=15)
        response.raise_for_status()
        
        # La nueva API devuelve los datos en la clave 'features'
        json_data = response.json().get("features", [])

        lista_estaciones = []

        for record in json_data:
            attributes = record.get("attributes", {})
            geometry = record.get("geometry", {})
            
            estacion = EstacionContaminacionAtmosferica()
            
            # Mapeo de atributos según requerimientos
            # 'nombre' suele ser más descriptivo en esta API, usamos 'direccion' como principal si existe
            estacion.direccion = attributes.get("direccion") or attributes.get("nombre") or "-"
            estacion.no2 = attributes.get("no2", "-")
            estacion.pm10 = attributes.get("pm10", "-")
            estacion.o3 = attributes.get("o3", "-")
            
            # Tratamiento de fecha (ArcGIS devuelve timestamp en ms)
            fecha_raw = attributes.get("fecha_carg")
            if isinstance(fecha_raw, (int, float)):
                try:
                    # Convertir ms a segundos y luego a string ISO para compatibilidad con el resto de la app
                    dt = datetime.datetime.fromtimestamp(fecha_raw / 1000.0)
                    estacion.fecha_carg = dt.isoformat()
                except:
                    estacion.fecha_carg = str(fecha_raw)
            else:
                estacion.fecha_carg = fecha_raw or "-"

            estacion.calidad_am = attributes.get("calidad_am", "-")
            
            # Coordenadas para el marcador: {lat: y, lon: x}
            if geometry:
                estacion.geo_point_2d = {
                    "lat": geometry.get("y"),
                    "lon": geometry.get("x")
                }

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
