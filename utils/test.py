import meteostat
from datetime import datetime
from meteostat import Point, monthly
import pandas as pd

# Valencia, Spain coordinates
valencia = Point(39.4699, -0.3763, 113)

# Month to query (December 2018)
start = datetime(2018, 12, 1)
end = datetime(2018, 12, 31)

print(f"Obteniendo datos meteorológicos de Valencia")
print("-" * 80)

# Get nearby stations
estaciones = meteostat.stations.nearby(valencia, limit=100, radius=1000000)
print(estaciones)
print(f"Estaciones encontradas: {len(estaciones)}")

# Get monthly data using Monthly class
data = monthly(estaciones, start, end)
df = data.fetch()

# Select relevant columns: temperature and precipitation
if not df.empty:
    # Display columns: tavg (temp avg), tmin, tmax, prcp (precipitation)
    columns_to_show = ['tavg', 'tmin', 'tmax', 'prcp']
    available_columns = [col for col in columns_to_show if col in df.columns]

    print(f"\nDatos diarios (Temperatura en °C, Precipitación en mm):")
    print("-" * 80)
    print(df[available_columns].to_string())

    # Summary statistics
    print("\n" + "=" * 80)
    print("RESUMEN DEL MES:")
    print("=" * 80)

    if 'tavg' in df.columns:
        avg_temp = df['tavg'].mean()
        if not pd.isna(avg_temp):
            print(f"Temperatura promedio: {avg_temp:.2f}°C")
    if 'tmin' in df.columns:
        min_temp = df['tmin'].min()
        if not pd.isna(min_temp):
            print(f"Temperatura mínima: {min_temp:.2f}°C")
    if 'tmax' in df.columns:
        max_temp = df['tmax'].max()
        if not pd.isna(max_temp):
            print(f"Temperatura máxima: {max_temp:.2f}°C")
    if 'prcp' in df.columns:
        total_prcp = df['prcp'].sum()
        days_with_rain = (df['prcp'] > 0).sum()
        if not pd.isna(total_prcp):
            print(f"Precipitación total: {total_prcp:.2f} mm")
            print(f"Días con precipitación: {days_with_rain} días")
else:
    print("\nNo se encontraron datos para el período especificado.")
