"""
Módulo utils para Data Detective.
"""

# Exportar funciones del data service
from .data_service import (
    get_cached_weather_data,
    get_cached_air_quality_data,
    get_cached_traffic_data,
    get_latest_sensor_data,
    clear_cache,
    get_cache_info
)

__all__ = [
    'get_cached_weather_data',
    'get_cached_air_quality_data',
    'get_cached_traffic_data',
    'get_latest_sensor_data',
    'clear_cache',
    'get_cache_info'
]
