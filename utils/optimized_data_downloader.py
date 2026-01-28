"""
Optimized data downloader that converts directly to JSON without intermediate CSV.
Uses multithreading for faster processing.
"""

import csv
import json
import os
import time
import threading
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Coordenadas aproximadas de estaciones de Valencia
STATION_COORDINATES = {
    'PISTA': {'lat': 39.4589, 'lon': -0.3768},
    'MOLÍ': {'lat': 39.4891, 'lon': -0.3800},
    'POLITÈCNIC': {'lat': 39.4811, 'lon': -0.3400},
    'VIVERS': {'lat': 39.4795, 'lon': -0.3667},
    'FRANÇA': {'lat': 39.4600, 'lon': -0.3500},
    'BULEVARD': {'lat': 39.4470, 'lon': -0.3600},
    'CENTRO': {'lat': 39.4702, 'lon': -0.3769},
    'OLIVERETA': {'lat': 39.4700, 'lon': -0.4000},
    'PATRAIX': {'lat': 39.4600, 'lon': -0.3900},
    'CABANYAL': {'lat': 39.4700, 'lon': -0.3300},
    'LLUCH': {'lat': 39.4700, 'lon': -0.3300},
    'VLC': {'lat': 39.4700, 'lon': -0.3700},
    'VALENCIA': {'lat': 39.4700, 'lon': -0.3700},
}


def get_station_coords(station_name):
    """Obtiene coordenadas para una estación basándose en su nombre."""
    name_upper = station_name.upper()

    # Búsqueda por palabra clave prioritaria
    for key, coords in STATION_COORDINATES.items():
        if key in name_upper:
            return coords

    # Si no se encuentra, retornar coordenadas por defecto de Valencia
    return {'lat': 39.4700, 'lon': -0.3700}


def download_and_convert_to_json(progress_callback=None):
    """
    Descarga datos históricos y los convierte directamente a JSON.

    Args:
        progress_callback: Función callback(current, total, message) para actualizar progreso

    Returns:
        bool: True si fue exitoso, False en caso contrario
    """
    from utils.GetContaminacio import get_historical_data

    # Configuración
    START_YEAR = 1994
    START_MONTH = 4
    END_YEAR = 2025
    END_MONTH = 11

    # Calcular total de meses
    total_months = (END_YEAR - START_YEAR) * 12 + (END_MONTH - START_MONTH) + 1

    # Estructura para almacenar datos por año
    years_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
        'nombre': '',
        'lat': '',
        'lon': '',
        'no2_values': [],
        'o3_values': [],
        'pm10_values': []
    })))

    # Metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'total_records': 0,
        'years': set(),
        'year_month_ranges': {}
    }

    # Lock para thread-safe operations
    data_lock = threading.Lock()
    downloaded_count = 0

    def process_month(year, month):
        """Descarga y procesa un mes específico."""
        nonlocal downloaded_count

        # Verificar si ya existe
        expected_filename = f"contaminacion_{year}_{month:02d}.csv"
        csv_dir = "csv_contaminacion"
        filepath = os.path.join(csv_dir, expected_filename)

        try:
            # Descargar si no existe
            if not os.path.exists(filepath):
                filepath = get_historical_data(year, month)
                time.sleep(0.3)  # Pequeña pausa para no saturar el servidor

            if not filepath or not os.path.exists(filepath):
                return None

            # Procesar el archivo CSV
            month_records = 0
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    # Filtrar solo Valencia
                    station_name = row.get('NOM_ESTACION', '').strip().upper()
                    if not any(kw in station_name for kw in ['VALENCIA', 'VLC', 'PISTA', 'MOLÍ', 'POLITÈCNIC', 'VIVERS', 'FRANÇA', 'BULEVARD']):
                        continue

                    # Verificar si tiene datos relevantes
                    has_data = False
                    for pollutant in ['NO2', 'O3', 'PM10']:
                        value = row.get(pollutant, '').strip()
                        if value and value != '-':
                            has_data = True
                            break

                    if not has_data:
                        continue

                    cod_estacion = row.get('COD_ESTACION', '').strip()
                    if not cod_estacion:
                        continue

                    # Agregar a estructura de datos (thread-safe)
                    with data_lock:
                        sensor = years_data[year][month][cod_estacion]

                        if not sensor['nombre']:
                            station_name = row.get('NOM_ESTACION', '').strip()
                            sensor['nombre'] = station_name

                            # Obtener coordenadas basadas en el nombre
                            coords = get_station_coords(station_name)
                            sensor['lat'] = coords['lat']
                            sensor['lon'] = coords['lon']

                        # Agregar valores
                        for pollutant, key in [('NO2', 'no2_values'), ('O3', 'o3_values'), ('PM10', 'pm10_values')]:
                            value = row.get(pollutant, '-').strip()
                            if value and value != '-':
                                try:
                                    sensor[key].append(float(value))
                                except ValueError:
                                    pass

                        metadata['years'].add(year)
                        month_records += 1

            # Actualizar progreso
            with data_lock:
                downloaded_count += 1
                if progress_callback:
                    progress_callback(downloaded_count, total_months, f"Procesado {
                                      year}-{month:02d}")

            return month_records

        except Exception as e:
            print(f"Error procesando {year}-{month:02d}: {e}")
            with data_lock:
                downloaded_count += 1
                if progress_callback:
                    progress_callback(downloaded_count, total_months, f"Error en {
                                      year}-{month:02d}")
            return None

    # Generar lista de meses a procesar
    months_to_process = []
    current_year = START_YEAR
    current_month = START_MONTH

    while current_year < END_YEAR or (current_year == END_YEAR and current_month <= END_MONTH):
        months_to_process.append((current_year, current_month))
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    print(f"📥 Procesando {len(months_to_process)} meses con multithreading...")

    # Procesar en paralelo con ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_month, year, month): (year, month)
                   for year, month in months_to_process}

        for future in as_completed(futures):
            result = future.result()
            # El progreso ya se actualiza dentro de process_month

    print(f"\n✅ Descarga completada: {
          downloaded_count}/{total_months} meses procesados")

    # Guardar archivos JSON por año
    project_root = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(project_root, "data", "pollution_historical")
    os.makedirs(output_dir, exist_ok=True)

    if progress_callback:
        progress_callback(total_months, total_months,
                          "💾 Guardando archivos JSON...")

    for year in sorted(metadata['years']):
        year_file = os.path.join(output_dir, f"{year}.json")

        year_structure = {
            'year': year,
            'months': {}
        }

        months_in_year = sorted(years_data[year].keys())
        metadata['year_month_ranges'][str(year)] = {
            'min': min(months_in_year) if months_in_year else 1,
            'max': max(months_in_year) if months_in_year else 12
        }

        for month in months_in_year:
            year_structure['months'][str(month)] = dict(
                years_data[year][month])

        with open(year_file, 'w', encoding='utf-8') as f:
            json.dump(year_structure, f, ensure_ascii=False, indent=2)

        print(f"  ✅ {year}.json creado")

    # Guardar metadata
    metadata['years'] = sorted(list(metadata['years']))
    metadata['total_records'] = sum(
        len(years_data[y][m])
        for y in years_data
        for m in years_data[y]
    )

    metadata_file = os.path.join(output_dir, 'metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Conversión completada!")
    print(f"📁 Archivos generados en: {output_dir}")
    print(f"📊 Total de años: {len(metadata['years'])}")

    return True


if __name__ == "__main__":
    def print_progress(current, total, message):
        print(f"[{current}/{total}] {message}")

    download_and_convert_to_json(progress_callback=print_progress)
