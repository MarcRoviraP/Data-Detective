import time
import pandas as pd
import os
import requests

def clean_description(description):
    description = description.split("[")[0]
    description = description.split("(")[0]
    return description.strip()

# Leer parquet
df = pd.read_parquet(
    os.path.join('data', 'trafico_valencia.parquet'),
    engine='pyarrow',
    filters=[('FECHA', '==', '2016-03')]
)

# Seleccionar columnas
df = df[["ATA", "DESCRIPCION"]]

# limpiar texto
df["DESCRIPCION"] = df["DESCRIPCION"].apply(clean_description)

# columnas nuevas
df["LON"] = None
df["LAT"] = None

print(df.head())

def getCoords(query):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query + " Valencia Spain",
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "traffic-coords-script/1.0"
    }

    response = requests.get(url, params=params, headers=headers)

    data = response.json()

    if data:
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        return lat, lon
    else:
        return None, None


for index, row in df.iterrows():

    time.sleep(1)

    try:
        lat, lon = getCoords(row["DESCRIPCION"])
        if lat is None or lon is None:
            continue
        df.loc[index, "LON"] = lon
        df.loc[index, "LAT"] = lat

        print(row["DESCRIPCION"], lat, lon)

    except Exception as e:
        print("Error:", row["DESCRIPCION"], e)

print(df)
df.to_parquet(os.path.join('data', 'trafico_valencia_coords.parquet'), engine='pyarrow')