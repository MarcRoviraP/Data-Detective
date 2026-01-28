"""
Servicio centralizado para obtener datos de sensores y APIs externas.
"""

import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .RealTimeValencianWeather import get_weather_data, Clima
from .RealTimeAirValencia import get_air_quality_data, EstacionContaminacionAtmosferica
from .GetContaminacio import get_historical_data
from .RealTimeTrafficValencia import get_traffic_data, EstacionTrafico


class DataCache:
    """Caché simple para evitar requests excesivos."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché si no ha expirado."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Guarda un valor en el caché."""
        self._cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Limpia todo el caché."""
        self._cache.clear()


# Caché global con TTL de 5 minutos
_cache = DataCache(ttl_seconds=300)


def get_cached_weather_data() -> List[Clima]:
    """
    Obtiene datos meteorológicos con caché.
    
    Returns:
        Lista de objetos Clima con datos de estaciones meteorológicas.
    """
    cached = _cache.get("weather_data")
    if cached is not None:
        print("📦 Usando datos meteorológicos en caché")
        return cached
    
    print("🌐 Obteniendo datos meteorológicos frescos...")
    data = get_weather_data()
    if data:
        _cache.set("weather_data", data)
    return data


def get_cached_air_quality_data() -> List[EstacionContaminacionAtmosferica]:
    """
    Obtiene datos de calidad del aire con caché.
    
    Returns:
        Lista de objetos EstacionContaminacionAtmosferica.
    """
    cached = _cache.get("air_quality_data")
    if cached is not None:
        print("📦 Usando datos de calidad del aire en caché")
        return cached
    
    print("🌐 Obteniendo datos de calidad del aire frescos...")
    data = get_air_quality_data()
    if data:
        _cache.set("air_quality_data", data)
    return data


def get_cached_traffic_data() -> List[EstacionTrafico]:
    """
    Obtiene datos de tráfico con caché.
    
    Returns:
        Lista de objetos EstacionTrafico.
    """
    cached = _cache.get("traffic_data")
    if cached is not None:
        print("📦 Usando datos de tráfico en caché")
        return cached
    
    print("🌐 Obteniendo datos de tráfico frescos...")
    data = get_traffic_data()
    if data:
        _cache.set("traffic_data", data)
    return data


def get_latest_sensor_data() -> Dict[str, Any]:
    """
    Obtiene los datos más recientes de todos los sensores.
    
    Returns:
        Diccionario con datos de clima, calidad del aire y tráfico.
    """
    return {
        "weather": get_cached_weather_data(),
        "air_quality": get_cached_air_quality_data(),
        "traffic": get_cached_traffic_data(),
        "timestamp": datetime.now().isoformat()
    }


def clear_cache() -> None:
    """Limpia el caché de datos."""
    _cache.clear()
    print("🗑️ Caché limpiado")


def get_cache_info() -> Dict[str, Any]:
    """
    Obtiene información sobre el estado del caché.
    
    Returns:
        Diccionario con información del caché.
    """
    return {
        "ttl_seconds": _cache.ttl_seconds,
        "cached_keys": list(_cache._cache.keys()),
        "cache_size": len(_cache._cache)
    }
