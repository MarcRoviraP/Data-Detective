"""
Script para obtener datos de tráfico en tiempo real de Valencia Open Data.
"""

import requests
from typing import List, Optional


class EstacionTrafico:
    """Clase para representar una estación de tráfico."""
    
    def __init__(self, data: dict):
        self.id = data.get("idtramo", "")
        self.denominacion = data.get("denominacion", "")
        self.estado = data.get("estado", "")
        self.intensidad = data.get("intensidad", "-")
        self.ocupacion = data.get("ocupacion", "-")
        self.carga = data.get("carga", "-")
        self.velocidad = data.get("velocidad", "-")
        
        # Coordenadas GPS
        geo = data.get("geo_point_2d", {})
        if isinstance(geo, dict):
            self.geo_point_2d = geo
        else:
            self.geo_point_2d = None
    
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
    Obtiene datos de tráfico en tiempo real de Valencia Open Data.
    
    Returns:
        Lista de objetos EstacionTrafico con datos de tráfico.
    """
    url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estat-transit-temps-real-estado-trafico-tiempo-real/records"
    
    params = {
        "limit": 100,
        "timezone": "Europe/Madrid"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        estaciones = []
        
        for record in data.get("results", []):
            estacion = EstacionTrafico(record)
            estaciones.append(estacion)
        
        return estaciones
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener datos de tráfico: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
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
