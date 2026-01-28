"""
Coordenadas GPS de estaciones AVAMET en Valencia.
Datos obtenidos de la plataforma MeteoXarxaOnline (MXO) de AVAMET.
"""

# Diccionario con coordenadas GPS de estaciones AVAMET en Valencia
AVAMET_STATIONS_COORDS = {
    "València Altocúmulo": {"lat": 39.4768, "lon": -0.3907},
    "València Carpesa Alqueries del Pelut": {"lat": 39.5167, "lon": -0.3667},
    "València Albors": {"lat": 39.4833, "lon": -0.3500},
    "València Benimaclet": {"lat": 39.4833, "lon": -0.3667},
    "València Camins al Grau": {"lat": 39.4667, "lon": -0.3500},
    "València l'Olivereta": {"lat": 39.4667, "lon": -0.3833},
    "València Micalet": {"lat": 39.4750, "lon": -0.3750},
    "València Patraix": {"lat": 39.4500, "lon": -0.3833},
    "València Penya-roja": {"lat": 39.4833, "lon": -0.4000},
}


def get_station_coordinates(station_name: str) -> dict:
    """
    Obtiene las coordenadas GPS de una estación AVAMET.
    
    Args:
        station_name: Nombre de la estación
        
    Returns:
        Diccionario con lat y lon, o None si no se encuentra
    """
    # Buscar coincidencia exacta
    if station_name in AVAMET_STATIONS_COORDS:
        return AVAMET_STATIONS_COORDS[station_name]
    
    # Buscar coincidencia parcial
    for key in AVAMET_STATIONS_COORDS:
        if station_name.lower() in key.lower() or key.lower() in station_name.lower():
            return AVAMET_STATIONS_COORDS[key]
    
    return None


def get_all_stations() -> dict:
    """
    Obtiene todas las estaciones con sus coordenadas.
    
    Returns:
        Diccionario completo de estaciones
    """
    return AVAMET_STATIONS_COORDS.copy()
