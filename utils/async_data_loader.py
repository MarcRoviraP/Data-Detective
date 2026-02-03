"""
Cargador asíncrono de datos para mejorar el tiempo de arranque.
Permite cargar datos históricos en threads separados con callbacks de progreso.
"""

import threading
import json
import os
from typing import Callable, Optional, Dict, Any
import traceback


class AsyncDataLoader:
    """Cargador asíncrono de datos con soporte para callbacks de progreso."""

    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Inicializa el cargador asíncrono.
        
        Args:
            progress_callback: Función opcional para reportar progreso (recibe mensaje de estado)
        """
        self.progress_callback = progress_callback
        self.pollution_data = None
        self.aemet_data = None
        self.weather_stations = None
        self.loading_errors = []
        self._lock = threading.Lock()

    def _report_progress(self, message: str):
        """Reporta progreso si hay callback configurado."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except Exception as e:
                print(f"⚠️ Error en callback de progreso: {e}")

    def load_pollution_data(self, json_base_path: str) -> Dict[str, Any]:
        """
        Carga metadata de datos históricos de contaminación.
        
        Args:
            json_base_path: Ruta base a la carpeta pollution_historical
            
        Returns:
            Dict con 'metadata' y 'year_cache'
        """
        result = {
            'metadata': {},
            'year_cache': {}
        }

        try:
            self._report_progress("Cargando metadata de contaminación...")
            metadata_path = os.path.join(json_base_path, "metadata.json")

            if not os.path.exists(metadata_path):
                error_msg = f"❌ Archivo metadata no encontrado: {metadata_path}"
                print(error_msg)
                with self._lock:
                    self.loading_errors.append(error_msg)
                return result

            with open(metadata_path, 'r', encoding='utf-8') as f:
                result['metadata'] = json.load(f)

            years_count = len(result['metadata'].get('years', []))
            year_range = ""
            if years_count > 0:
                years = result['metadata']['years']
                year_range = f"{min(years)}-{max(years)}"
            
            success_msg = f"✅ Metadata de contaminación cargada: {years_count} años ({year_range})"
            print(success_msg)
            self._report_progress(success_msg)

        except Exception as e:
            error_msg = f"❌ Error al cargar metadata de contaminación: {e}"
            print(error_msg)
            print(traceback.format_exc())
            with self._lock:
                self.loading_errors.append(error_msg)

        with self._lock:
            self.pollution_data = result
        
        return result

    def load_aemet_data(self, aemet_dir: str, stations_path: str) -> Dict[str, Any]:
        """
        Carga datos históricos de AEMET y estaciones meteorológicas.
        
        Args:
            aemet_dir: Ruta al directorio aemet_historical
            stations_path: Ruta al archivo valencia_stations.json
            
        Returns:
            Dict con 'aemet_data' y 'weather_stations_info'
        """
        result = {
            'aemet_data': {},
            'weather_stations_info': {}
        }

        # Bounding box para Valencia Ciudad
        VALENCIA_BBOX = {
            "lat_min": 39.40,
            "lat_max": 39.55,
            "lon_min": -0.55,
            "lon_max": -0.25
        }

        try:
            # Cargar información de estaciones
            self._report_progress("Cargando estaciones meteorológicas...")
            
            if os.path.exists(stations_path):
                with open(stations_path, 'r', encoding='utf-8') as f:
                    stations = json.load(f)
                    
                for s in stations:
                    indicativo = s['indicativo']
                    lat = self._dms_to_decimal(s['latitud'])
                    lon = self._dms_to_decimal(s['longitud'])

                    # Filtrar solo estaciones dentro de Valencia Ciudad
                    if lat and lon:
                        if (VALENCIA_BBOX["lat_min"] <= lat <= VALENCIA_BBOX["lat_max"] and
                                VALENCIA_BBOX["lon_min"] <= lon <= VALENCIA_BBOX["lon_max"]):
                            result['weather_stations_info'][indicativo] = {
                                'nombre': s['nombre'],
                                'lat': lat,
                                'lon': lon
                            }
                
                stations_msg = f"✅ {len(result['weather_stations_info'])} estaciones meteorológicas cargadas"
                print(stations_msg)
                self._report_progress(stations_msg)

        except Exception as e:
            error_msg = f"❌ Error al cargar estaciones: {e}"
            print(error_msg)
            with self._lock:
                self.loading_errors.append(error_msg)

        try:
            # Cargar datos AEMET
            self._report_progress("Cargando datos históricos AEMET...")
            
            if not os.path.exists(aemet_dir):
                print(f"⚠️ Directorio AEMET no encontrado: {aemet_dir}")
                with self._lock:
                    self.aemet_data = result
                return result

            total_months = 0
            for filename in os.listdir(aemet_dir):
                if filename.startswith("monthly_") and filename.endswith(".json"):
                    parts = filename.split("_")
                    if len(parts) >= 2:
                        indicativo = parts[1]
                        try:
                            filepath = os.path.join(aemet_dir, filename)
                            with open(filepath, 'r', encoding='utf-8') as f:
                                raw_data = json.load(f)
                                if indicativo not in result['aemet_data']:
                                    result['aemet_data'][indicativo] = {}

                                for item in raw_data:
                                    if 'fecha' in item:
                                        result['aemet_data'][indicativo][item['fecha']] = item
                                        total_months += 1
                        except Exception as e:
                            print(f"⚠️ Error al cargar {filename}: {e}")

            aemet_msg = f"✅ Datos AEMET cargados: {total_months} registros de {len(result['aemet_data'])} estaciones"
            print(aemet_msg)
            self._report_progress(aemet_msg)

        except Exception as e:
            error_msg = f"❌ Error al cargar datos AEMET: {e}"
            print(error_msg)
            print(traceback.format_exc())
            with self._lock:
                self.loading_errors.append(error_msg)

        with self._lock:
            self.aemet_data = result
        
        return result

    def _dms_to_decimal(self, dms_str: str) -> Optional[float]:
        """
        Convierte coordenadas de formato AEMET (DDMMSSX) a decimal.
        
        Args:
            dms_str: String en formato DDMMSSX (ej: "392838N")
            
        Returns:
            Coordenada en formato decimal o None si hay error
        """
        try:
            if not dms_str or len(dms_str) < 7:
                return None

            direction = dms_str[-1]
            dms_str = dms_str[:-1]

            degrees = int(dms_str[0:2])
            minutes = int(dms_str[2:4])
            seconds = int(dms_str[4:6])

            decimal = degrees + minutes / 60 + seconds / 3600

            if direction in ['S', 'W', 'O']:
                decimal = -decimal

            return decimal
        except Exception:
            return None

    def load_all_async(
        self,
        json_base_path: str,
        aemet_dir: str,
        stations_path: str,
        on_complete: Optional[Callable[[bool], None]] = None
    ):
        """
        Carga todos los datos en threads paralelos.
        
        Args:
            json_base_path: Ruta base a pollution_historical
            aemet_dir: Ruta a aemet_historical
            stations_path: Ruta a valencia_stations.json
            on_complete: Callback cuando termine (recibe True si éxito, False si error)
        """
        def load_pollution():
            self.load_pollution_data(json_base_path)

        def load_aemet():
            self.load_aemet_data(aemet_dir, stations_path)

        def wait_and_notify():
            # Esperar a que ambos threads terminen
            pollution_thread.join()
            aemet_thread.join()
            
            # Notificar completado
            success = len(self.loading_errors) == 0
            if on_complete:
                try:
                    on_complete(success)
                except Exception as e:
                    print(f"⚠️ Error en callback de completado: {e}")

        # Iniciar threads de carga
        pollution_thread = threading.Thread(target=load_pollution, daemon=True)
        aemet_thread = threading.Thread(target=load_aemet, daemon=True)
        
        pollution_thread.start()
        aemet_thread.start()

        # Thread para esperar y notificar
        notify_thread = threading.Thread(target=wait_and_notify, daemon=True)
        notify_thread.start()

    def get_pollution_data(self) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de contaminación cargados (thread-safe)."""
        with self._lock:
            return self.pollution_data

    def get_aemet_data(self) -> Optional[Dict[str, Any]]:
        """Obtiene los datos AEMET cargados (thread-safe)."""
        with self._lock:
            return self.aemet_data

    def get_errors(self) -> list:
        """Obtiene la lista de errores durante la carga (thread-safe)."""
        with self._lock:
            return self.loading_errors.copy()
