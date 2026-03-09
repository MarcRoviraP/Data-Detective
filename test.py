import pandas as pd
import os
import pyarrow

# Leer el archivo
df = pd.read_parquet(
    os.path.join('data', 'trafico_valencia.parquet'), 
    engine='pyarrow',
    filters=[('FECHA', '==', '2016-03')]
)
print(df)