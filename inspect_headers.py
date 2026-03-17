import pandas as pd
import os
import glob

dir_ods = os.path.join(os.path.dirname(__file__), "data", "ods")
ficheros = glob.glob(os.path.join(dir_ods, "*.ods"))

for f in sorted(ficheros):
    nombre_fichero = os.path.basename(f)
    print(f"\n--- {nombre_fichero} ---")
    df = pd.read_excel(f, engine="calamine", nrows=0)
    print(df.columns.tolist())
