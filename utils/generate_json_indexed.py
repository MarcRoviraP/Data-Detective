"""
Script para convertir valencia_pollution_consolidated.csv a formato JSON fragmentado.
Genera un archivo JSON por año para búsquedas ultra-rápidas.
"""

import csv
import json
import os
from collections import defaultdict
from datetime import datetime


def csv_to_json_fragmented():
    """Convierte el CSV consolidado a archivos JSON fragmentados por año."""

    # Rutas
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "valencia_pollution_consolidated.csv")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                              "data", "pollution_historical")

    # Crear directorio si no existe
    os.makedirs(output_dir, exist_ok=True)

    print(f"📂 Leyendo CSV: {csv_path}")

    if not os.path.exists(csv_path):
        print(f"❌ Archivo CSV no encontrado: {csv_path}")
        return False

    # Estructura: {año: {mes: {cod_estacion: {datos}}}}
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

    record_count = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')

            for row in reader:
                record_count += 1

                # Parsear fecha
                fecha_str = row.get('FECHA', '')
                if not fecha_str:
                    continue

                parts = fecha_str.split('-')
                if len(parts) < 2:
                    continue

                year = int(parts[0])
                month = int(parts[1])

                cod_estacion = row.get('COD_ESTACION', '')
                if not cod_estacion:
                    continue

                # Agregar a metadata
                metadata['years'].add(year)

                # Inicializar sensor si no existe
                sensor = years_data[year][month][cod_estacion]

                if not sensor['nombre']:
                    sensor['nombre'] = row.get('NOM_ESTACION', '')
                    sensor['lat'] = row.get('LATITUD', '')
                    sensor['lon'] = row.get('LONGITUD', '')

                # Agregar valores
                no2 = row.get('NO2', '-')
                if no2 and no2 != '-':
                    try:
                        sensor['no2_values'].append(float(no2))
                    except ValueError:
                        pass

                o3 = row.get('O3', '-')
                if o3 and o3 != '-':
                    try:
                        sensor['o3_values'].append(float(o3))
                    except ValueError:
                        pass

                pm10 = row.get('PM10', '-')
                if pm10 and pm10 != '-':
                    try:
                        sensor['pm10_values'].append(float(pm10))
                    except ValueError:
                        pass

        print(f"✅ Procesados {record_count} registros")
        print(f"📊 Años encontrados: {sorted(metadata['years'])}")

        # Guardar cada año en un archivo separado
        for year in sorted(metadata['years']):
            year_file = os.path.join(output_dir, f"{year}.json")

            # Convertir defaultdict a dict normal para JSON
            year_structure = {
                'year': year,
                'months': {}
            }

            # Calcular rango de meses para este año
            months_in_year = sorted(years_data[year].keys())
            metadata['year_month_ranges'][str(year)] = {
                'min': min(months_in_year),
                'max': max(months_in_year)
            }

            for month in months_in_year:
                year_structure['months'][str(month)] = dict(
                    years_data[year][month])

            # Guardar archivo JSON
            with open(year_file, 'w', encoding='utf-8') as f:
                json.dump(year_structure, f, ensure_ascii=False, indent=2)

            month_count = len(year_structure['months'])
            sensor_count = sum(len(sensors)
                               for sensors in year_structure['months'].values())
            print(f"  ✅ {year}.json creado: {
                  month_count} meses, {sensor_count} sensores")

        # Guardar metadata
        metadata['total_records'] = record_count
        metadata['years'] = sorted(list(metadata['years']))

        metadata_file = os.path.join(output_dir, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Conversión completada!")
        print(f"📁 Archivos generados en: {output_dir}")
        print(f"📊 Total de años: {len(metadata['years'])}")
        print(f"📝 Registros procesados: {record_count}")

        return True

    except Exception as e:
        print(f"❌ Error durante la conversión: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Iniciando conversión CSV → JSON fragmentado\n")
    success = csv_to_json_fragmented()

    if success:
        print("\n🎉 ¡Conversión exitosa!")
    else:
        print("\n❌ La conversión falló")
