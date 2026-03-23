import pandas as pd
import os

path = r'c:\Users\Marc\Desktop\delte\Data-Detective\data\trafico_valencia_coords.parquet'
if os.path.exists(path):
    df = pd.read_parquet(path)
    print(f"Columns in {os.path.basename(path)}: {df.columns.tolist()}")
    print(df.head())
else:
    print(f"File not found: {path}")
