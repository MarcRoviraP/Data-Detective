import pandas as pd

df = pd.read_parquet('c:/Users/Marc/Desktop/delte/Data-Detective/data/trafico_valencia.parquet')
df_coords = pd.read_parquet('c:/Users/Marc/Desktop/delte/Data-Detective/data/trafico_valencia_coords.parquet')

date_str = "2019-02"
df_filtered = df[df['FECHA'] == date_str]

coords_dict = {}
for _, row in df_coords.iterrows():
    coords_dict[row['ATA']] = {
        'lat': row['LAT'],
        'lon': row['LON'],
        'desc': row['DESCRIPCION']
    }

markers_added = 0
errors = 0

for _, row in df_filtered.iterrows():
    try:
        ata_id = row['ATA']
        imd = row['IMD']
        
        coord = coords_dict.get(ata_id)
        desc = coord.get('desc', 'N/A') if coord else 'N/A'
        if not coord or pd.isna(coord['lat']) or pd.isna(coord['lon']):
            continue
        
        lat = coord['lat']
        lon = coord['lon']
        
        # Asignar color dinámico según intensidad (IMD)
        if pd.isna(imd):
            print(f"NaN IMD for {ata_id}")
            errors += 1
            continue

        try:
            imd_val = int(imd)
            markers_added += 1
        except Exception as e:
            print(f"Error int(imd) on {ata_id} with imd='{imd}': {e}")
            errors += 1
            continue
            
    except Exception as e:
        print(f"Error on {row['ATA']}: {e}")
        errors += 1

print(f"Total rows in df_filtered: {len(df_filtered)}")
print(f"Markers added: {markers_added}")
print(f"Errors found: {errors}")
