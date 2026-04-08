"""
Script para obtener datos de tráfico en tiempo real de Valencia Open Data.
"""

import requests
from typing import List, Optional


class EstacionTrafico:
    """Clase para representar una estación de tráfico."""
    
    def __init__(self, data: dict):
        # Mapeo sugerido por el usuario:
        # tramoId -> attributes.idtramo
        # descripcion -> attributes.des_tramo
        # intensidad -> attributes.lectura
        # estado -> attributes.estado
        # points -> geometry.paths
        
        attributes = data.get("attributes", {})
        geometry = data.get("geometry", {})
        
        self.id = attributes.get("idtramo", "")
        self.denominacion = attributes.get("denominacion") or attributes.get("des_tramo") or attributes.get("nombre") or ""
        self.estado = attributes.get("estado")
        self.intensidad = attributes.get("lectura", "-")
        
        # Otros campos que la app podría usar
        self.velocidad = attributes.get("velocidad", "-")
        self.ocupacion = attributes.get("ocupacion", "-")
        self.carga = attributes.get("carga", "-")
        
        # Geometría del tramo (lista de puntos para las líneas)
        self.points = geometry.get("paths", [])
        
        # Coordenadas geográficas (punto de referencia para marcadores)
        self.geo_point_2d = None
        if self.points and len(self.points) > 0 and len(self.points[0]) > 0:
            # Usamos el primer punto del primer path como referencia lat/lon
            first_point = self.points[0][0]
            if len(first_point) >= 2:
                self.geo_point_2d = {
                    "lon": first_point[0],
                    "lat": first_point[1]
                }
    
    def imprimir_informacion(self):
        """Imprime la información de la estación de tráfico."""
        print(f"\n{'='*50}")
        print(f"ID: {self.id}")
        print(f"Ubicación: {self.denominacion}")
        print(f"Estado: {self.estado}")
        print(f"Intensidad: {self.intensidad} veh/h")
        print(f"Ocupación: {self.ocupacion}%")
        print(f"Carga: {self.carga}")
        print(f"Velocidad: {self.velocidad} km/h")
        if self.geo_point_2d:
            print(f"Coordenadas: {self.geo_point_2d.get('lat')}, {self.geo_point_2d.get('lon')}")
        print(f"{'='*50}")


def get_estado_descripcion(codigo_estado):
    """
    Traduce el código de estado numérico a descripción textual.
    
    Args:
        codigo_estado: Código numérico del estado (0-9)
        
    Returns:
        Tupla (descripción, color_sugerido)
    """
    estados = {
        0: ("Fluido", "green"),
        1: ("Denso", "yellow"),
        2: ("Congestionado", "red"),
        3: ("Cortado", "red"),
        4: ("Sin datos", "gray"),
        5: ("Paso inferior fluido", "green"),
        6: ("Paso inferior denso", "yellow"),
        7: ("Paso inferior congestionado", "red"),
        8: ("Paso inferior cortado", "red"),
        9: ("Sin datos (paso inferior)", "gray")
    }
    
    try:
        codigo = int(codigo_estado)
        return estados.get(codigo, ("Desconocido", "gray"))
    except (ValueError, TypeError):
        return ("Sin información", "gray")



def get_traffic_data() -> List[EstacionTrafico]:
    """
    Obtiene datos de tráfico en tiempo real de Valencia ArcGIS Geoportal.
    
    Returns:
        Lista de objetos EstacionTrafico con datos de tráfico y geometría.
    """
    # URL ArcGIS para "Estat transit temps real" (ID 192)
    url = "https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/192/query"
    
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "json",
        "outSR": "4326",
        "resultRecordCount": 1000
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(response.url)
        response.raise_for_status()
        
        data = response.json()
        estaciones = []
        
        # En ArcGIS los datos vienen en 'features'
        for record in data.get("features", []):
            estacion = EstacionTrafico(record)
            estaciones.append(estacion)
        
        return estaciones
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener datos de tráfico: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado en get_traffic_data: {e}")
        return []


def main():
    """Función principal para pruebas."""
    print("🚗 Obteniendo datos de tráfico de Valencia...")
    
    estaciones = get_traffic_data()
    
    if estaciones:
        print(f"\n✅ Se encontraron {len(estaciones)} estaciones de tráfico")
        
        # Mostrar primeras 3 estaciones
        for i, estacion in enumerate(estaciones[:3], 1):
            print(f"\n--- Estación {i} ---")
            estacion.imprimir_informacion()
    else:
        print("\n❌ No se pudieron obtener datos de tráfico")


if __name__ == "__main__":
    main()
