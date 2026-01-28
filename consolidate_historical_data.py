"""
Script para descargar y consolidar datos históricos de contaminación de Valencia.
Descarga todos los meses desde 1994-04 hasta 2025-11 y crea un CSV consolidado
con solo NO2, O3 y PM10.
"""

import csv
import os
import time
from datetime import datetime
from utils.GetContaminacio import get_historical_data

# Configuración
START_YEAR = 1994
START_MONTH = 4
END_YEAR = 2025
END_MONTH = 11

OUTPUT_FILE = "valencia_pollution_consolidated.csv"
POLLUTANTS_TO_KEEP = ['NO2', 'O3', 'PM10']

# Estaciones de Valencia (puedes ajustar según necesites)
VALENCIA_STATIONS = [
    'VALENCIA',
    'VLC',
    'PISTA',
    'MOLÍ',
    'POLITÈCNIC',
    'VIVERS',
    'FRANÇA',
    'BULEVARD',
    'AVINGUDA',
    'CENTRO'
]


def is_valencia_station(station_name):
    """Verifica si una estación pertenece a Valencia."""
    if not station_name:
        return False
    
    station_upper = station_name.upper()
    
    # Buscar palabras clave de Valencia
    for keyword in VALENCIA_STATIONS:
        if keyword in station_upper:
            return True
    
    return False


def download_all_data():
    """Descarga todos los archivos CSV históricos."""
    print("=" * 60)
    print("📥 DESCARGANDO DATOS HISTÓRICOS DE CONTAMINACIÓN")
    print("=" * 60)
    print(f"Período: {START_YEAR}-{START_MONTH:02d} hasta {END_YEAR}-{END_MONTH:02d}")
    print(f"Contaminantes: {', '.join(POLLUTANTS_TO_KEEP)}")
    print("=" * 60)
    
    downloaded_files = []
    failed_downloads = []
    
    current_year = START_YEAR
    current_month = START_MONTH
    
    total_months = (END_YEAR - START_YEAR) * 12 + (END_MONTH - START_MONTH) + 1
    month_count = 0
    
    while current_year < END_YEAR or (current_year == END_YEAR and current_month <= END_MONTH):
        month_count += 1
        print(f"\n[{month_count}/{total_months}] Descargando {current_year}-{current_month:02d}...", end=" ")
        
        try:
            filepath = get_historical_data(current_year, current_month)
            
            if filepath and os.path.exists(filepath):
                downloaded_files.append(filepath)
                print(f"✅ OK")
            else:
                failed_downloads.append(f"{current_year}-{current_month:02d}")
                print(f"⚠️ No disponible")
        
        except Exception as e:
            failed_downloads.append(f"{current_year}-{current_month:02d}")
            print(f"❌ Error: {e}")
        
        # Avanzar al siguiente mes
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
        
        # Pequeña pausa para no saturar el servidor
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"✅ Descargados: {len(downloaded_files)} archivos")
    print(f"⚠️ Fallidos: {len(failed_downloads)} archivos")
    
    if failed_downloads:
        print(f"\nMeses sin datos: {', '.join(failed_downloads[:10])}")
        if len(failed_downloads) > 10:
            print(f"... y {len(failed_downloads) - 10} más")
    
    print("=" * 60)
    
    return downloaded_files


def consolidate_data(csv_files):
    """Consolida todos los CSVs en uno solo con filtros aplicados."""
    print("\n" + "=" * 60)
    print("🔄 CONSOLIDANDO DATOS")
    print("=" * 60)
    
    consolidated_rows = []
    total_rows_processed = 0
    total_rows_kept = 0
    
    # Encabezados del CSV consolidado
    headers = ['COD_ESTACION', 'NOM_ESTACION', 'FECHA', 'NO2', 'O3', 'PM10']
    
    for i, filepath in enumerate(csv_files, 1):
        print(f"[{i}/{len(csv_files)}] Procesando {os.path.basename(filepath)}...", end=" ")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                file_rows_kept = 0
                
                for row in reader:
                    total_rows_processed += 1
                    
                    # Filtrar solo estaciones de Valencia
                    station_name = row.get('NOM_ESTACION', '').strip()
                    if not is_valencia_station(station_name):
                        continue
                    
                    # Verificar si tiene al menos uno de los contaminantes
                    has_data = False
                    for pollutant in POLLUTANTS_TO_KEEP:
                        value = row.get(pollutant, '').strip()
                        if value and value != '-':
                            has_data = True
                            break
                    
                    if not has_data:
                        continue
                    
                    # Crear fila consolidada
                    consolidated_row = {
                        'COD_ESTACION': row.get('COD_ESTACION', '').strip(),
                        'NOM_ESTACION': station_name,
                        'FECHA': row.get('FECHA', '').strip(),
                        'NO2': row.get('NO2', '-').strip(),
                        'O3': row.get('O3', '-').strip(),
                        'PM10': row.get('PM10', '-').strip()
                    }
                    
                    consolidated_rows.append(consolidated_row)
                    file_rows_kept += 1
                    total_rows_kept += 1
                
                print(f"✅ {file_rows_kept} filas")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    print("=" * 60)
    print(f"📊 Total procesado: {total_rows_processed:,} filas")
    print(f"✅ Total consolidado: {total_rows_kept:,} filas")
    print(f"📉 Filtrado: {total_rows_processed - total_rows_kept:,} filas")
    print("=" * 60)
    
    return headers, consolidated_rows


def save_consolidated_csv(headers, rows):
    """Guarda el CSV consolidado."""
    print(f"\n💾 Guardando archivo consolidado: {OUTPUT_FILE}")
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
        
        file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)  # MB
        print(f"✅ Archivo guardado: {OUTPUT_FILE}")
        print(f"📦 Tamaño: {file_size:.2f} MB")
        print(f"📝 Filas: {len(rows):,}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error al guardar: {e}")
        return False


def generate_summary(rows):
    """Genera un resumen estadístico del dataset consolidado."""
    print("\n" + "=" * 60)
    print("📈 RESUMEN ESTADÍSTICO")
    print("=" * 60)
    
    # Contar por año
    years = {}
    stations = set()
    
    for row in rows:
        fecha = row.get('FECHA', '')
        if fecha:
            year = fecha.split('-')[0]
            years[year] = years.get(year, 0) + 1
        
        station = row.get('NOM_ESTACION', '')
        if station:
            stations.add(station)
    
    print(f"\n📅 Años con datos: {len(years)}")
    print(f"🏢 Estaciones únicas: {len(stations)}")
    
    print(f"\n📊 Distribución por año:")
    for year in sorted(years.keys()):
        count = years[year]
        bar = "█" * min(50, count // 10)
        print(f"  {year}: {count:>5} filas {bar}")
    
    print(f"\n🏢 Estaciones de Valencia:")
    for station in sorted(stations):
        print(f"  • {station}")
    
    print("=" * 60)


def main():
    """Función principal."""
    start_time = time.time()
    
    print("\n🚀 INICIANDO CONSOLIDACIÓN DE DATOS HISTÓRICOS")
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Paso 1: Descargar todos los archivos
    csv_files = download_all_data()
    
    if not csv_files:
        print("\n❌ No se descargaron archivos. Abortando.")
        return
    
    # Paso 2: Consolidar datos
    headers, consolidated_rows = consolidate_data(csv_files)
    
    if not consolidated_rows:
        print("\n⚠️ No se encontraron datos de Valencia para consolidar.")
        return
    
    # Paso 3: Guardar CSV consolidado
    if save_consolidated_csv(headers, consolidated_rows):
        # Paso 4: Generar resumen
        generate_summary(consolidated_rows)
    
    # Tiempo total
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print(f"\n✅ PROCESO COMPLETADO")
    print(f"⏱️ Tiempo total: {minutes}m {seconds}s")
    print(f"📁 Archivo generado: {OUTPUT_FILE}\n")


if __name__ == "__main__":
    main()
