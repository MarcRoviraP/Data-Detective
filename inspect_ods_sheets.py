import pandas as pd
import os

file_path = r'c:\Users\Marc\Desktop\delte\Data-Detective\data\ods\imds 2019.ods'
try:
    xl = pd.ExcelFile(file_path) # Let pandas decide
    print(f"Sheets in {os.path.basename(file_path)}:")
    for sheet_name in xl.sheet_names:
        print(f" - {sheet_name}")
        df = xl.parse(sheet_name)
        print(f"   Columns: {df.columns.tolist()[:10]}...")
except Exception as e:
    print(f"Error reading {file_path} with default engine: {e}")
    try:
        xl = pd.ExcelFile(file_path, engine='odf')
        print(f"Sheets in {os.path.basename(file_path)} (odf):")
        for sheet_name in xl.sheet_names:
            print(f" - {sheet_name}")
    except Exception as e2:
        print(f"Error reading with odf: {e2}")
