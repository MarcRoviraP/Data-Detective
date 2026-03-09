import pandas as pd
import os
import glob
import re

dir_ods = os.path.join(os.path.dirname(__file__), "data", "ods")
archivo_salida = os.path.join(os.path.dirname(__file__), "data", "trafico_valencia.parquet")

def procesar_imds():
    ficheros = glob.glob(os.path.join(dir_ods, "*.ods"))
    lista_acumulada = []

    for f in ficheros:
        nombre_fichero = os.path.basename(f)
        print(f"Procesando: {nombre_fichero}")
        
        # Extraer el año del nombre del archivo (ej: 2016)
        anio_match = re.search(r'(\d{4})', nombre_fichero)
        anio_doc = anio_match.group(1) if anio_match else "0000"

        df = pd.read_excel(f, engine="calamine")
        df.columns = df.columns.astype(str).str.strip()

        # 1. Normalizar columna de Descripción
        df = df.rename(columns={c: 'DESCRIPCION' for c in df.columns if 'DESCRIP' in c.upper()})

        # 2. Identificar columnas de datos (meses o IMD general)
        # Formato antiguo: tramos_imd 2016-01.IMD [cite: 1]
        cols_meses = [c for c in df.columns if '.IMD' in c and '-' in c]
        
        # Formato nuevo: 'IMD Laborables', 'IMD Lab.', etc. [cite: 10, 11]
        cols_generales = [c for c in df.columns if 'IMD' in c.upper() and '-' not in c]

        if cols_meses:
            # Caso archivos viejos (unión por meses)
            df_largo = df.melt(
                id_vars=['ATA', 'DESCRIPCION'],
                value_vars=cols_meses,
                var_name='FECHA_RAW',
                value_name='IMD'
            )
            df_largo['FECHA'] = df_largo['FECHA_RAW'].str.extract(r'(\d{4}-\d{2})')
        else:
            # Caso archivos nuevos (dato anual o único)
            df_largo = df.copy()
            # Usamos la primera columna de IMD encontrada
            col_valor = cols_generales[0] if cols_generales else None
            if col_valor:
                df_largo = df_largo.rename(columns={col_valor: 'IMD'})
                df_largo['FECHA'] = f"{anio_doc}-01" # Asignamos enero del año del doc
                df_largo = df_largo[['ATA', 'DESCRIPCION', 'IMD', 'FECHA']]

        lista_acumulada.append(df_largo)

    if lista_acumulada:
        df_final = pd.concat(lista_acumulada, ignore_index=True)
        # Limpieza final de nulos y tipos
        df_final['IMD'] = pd.to_numeric(df_final['IMD'], errors='coerce').fillna(0)
        df_final.to_parquet(archivo_salida, index=False)
        print(f"✅ Proceso completado: {len(df_final)} registros unificados.")
    else:
        print("❌ No se encontraron datos válidos.")

if __name__ == "__main__":
    procesar_imds()