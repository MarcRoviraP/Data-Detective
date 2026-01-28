"""
Procesador de datos históricos de contaminación.
"""

import csv
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class HistoricalDataProcessor:
    """Procesa datos históricos de contaminación desde archivos CSV."""
    
    def __init__(self, csv_path: str):
        """
        Inicializa el procesador con un archivo CSV.
        
        Args:
            csv_path: Ruta al archivo CSV de datos históricos
        """
        self.csv_path = csv_path
        self.data = []
        self.statistics = {}
        
    def load_data(self, year: int = None, month: int = None) -> bool:
        """
        Carga datos desde el archivo CSV, filtrando por año y mes opcionalmente.
        
        Args:
            year: Año a filtrar (opcional)
            month: Mes a filtrar (opcional)
            
        Returns:
            True si se cargó correctamente, False en caso contrario
        """
        try:
            if not os.path.exists(self.csv_path):
                print(f"⚠️ Archivo no encontrado: {self.csv_path}")
                return False
            
            self.data = []
            filter_prefix = ""
            if year:
                filter_prefix = f"{year}"
                if month:
                    filter_prefix = f"{year}-{month:02d}"
            
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                for row in reader:
                    fecha = row.get('FECHA', '')
                    if not fecha:
                        continue
                        
                    # Filtrado rápido por string de fecha (YYYY-MM-DD)
                    if filter_prefix and not fecha.startswith(filter_prefix):
                        continue
                        
                    self.data.append(row)
            
            print(f"✅ Cargados {len(self.data)} registros para {filter_prefix} desde {os.path.basename(self.csv_path)}")
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar datos: {e}")
            return False
    
    def calculate_statistics(self) -> Dict:
        """
        Calcula estadísticas de los datos cargados.
        
        Returns:
            Diccionario con estadísticas por contaminante
        """
        if not self.data:
            return {}
        
        # Contaminantes principales a analizar presentes en el consolidado
        pollutant_columns = ['NO2', 'O3', 'PM10']
        
        # Agrupar por contaminante
        pollutants = defaultdict(list)
        
        for row in self.data:
            for pollutant in pollutant_columns:
                value_str = row.get(pollutant, '').strip()
                
                if value_str and value_str != '-':
                    try:
                        # Reemplazar coma por punto para decimales (si quedaron)
                        value = float(value_str.replace(',', '.'))
                        if value >= 0:  # Datos válidos
                            pollutants[pollutant].append(value)
                    except ValueError:
                        continue
        
        # Calcular estadísticas por contaminante
        stats = {}
        for pollutant, values in pollutants.items():
            if values:
                stats[pollutant] = {
                    'avg': sum(values) / len(values),
                    'max': max(values),
                    'min': min(values),
                    'count': len(values),
                    'values': values  # Guardar para análisis adicional
                }
        
        self.statistics = stats
        return stats
    
    def get_daily_averages(self, pollutant: str) -> List[Tuple[str, float]]:
        """
        Obtiene valores diarios promedios (si hay varias estaciones) para un contaminante.
        """
        daily_values = defaultdict(list)
        
        for row in self.data:
            fecha = row.get('FECHA', '').strip()
            if not fecha:
                continue
            
            value_str = row.get(pollutant, '').strip()
            if value_str and value_str != '-':
                try:
                    value = float(value_str.replace(',', '.'))
                    if value >= 0:
                        daily_values[fecha].append(value)
                except ValueError:
                    continue
        
        # Promediar por día (entre todas las estaciones)
        result = []
        for fecha, values in sorted(daily_values.items()):
            if values:
                avg = sum(values) / len(values)
                result.append((fecha, avg))
                
        return result
    
    def get_station_comparison(self, pollutant: str) -> Dict[str, float]:
        """Compara niveles de contaminante entre estaciones."""
        station_data = defaultdict(list)
        
        for row in self.data:
            estacion = row.get('NOM_ESTACION', '').strip()
            if not estacion:
                continue
            
            value_str = row.get(pollutant, '').strip()
            if value_str and value_str != '-':
                try:
                    value = float(value_str.replace(',', '.'))
                    if value >= 0:
                        station_data[estacion].append(value)
                except ValueError:
                    continue
        
        station_averages = {}
        for station, values in station_data.items():
            if values:
                station_averages[station] = sum(values) / len(values)
        
        return station_averages

    def get_peak_hours(self, pollutant: str) -> Dict[int, float]:
        """No aplica para datos diarios."""
        return {}
    
    def get_data_completeness(self) -> float:
        """Calcula el porcentaje de completitud (celdas con valor vs total celdas posibles)."""
        if not self.data:
            return 0.0
        
        pollutant_columns = ['NO2', 'O3', 'PM10']
        total_cells = len(self.data) * len(pollutant_columns)
        filled_cells = 0
        
        for row in self.data:
            for pollutant in pollutant_columns:
                value_str = row.get(pollutant, '').strip()
                if value_str and value_str != '-':
                    filled_cells += 1
        
        if total_cells == 0:
            return 0.0
        
        return (filled_cells / total_cells) * 100


def get_latest_historical_file() -> Optional[str]:
    """
    Busca el archivo CSV más reciente en la carpeta csv_contaminacion.
    
    Returns:
        Ruta al archivo más reciente o None
    """
    csv_dir = "csv_contaminacion"
    
    if not os.path.exists(csv_dir):
        return None
    
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    
    if not csv_files:
        return None
    
    # Ordenar por fecha de modificación (más reciente primero)
    csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(csv_dir, x)), reverse=True)
    
    return os.path.join(csv_dir, csv_files[0])
