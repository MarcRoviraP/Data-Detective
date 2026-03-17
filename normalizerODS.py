import pandas as pd
import os
import glob
import re
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "normalizer.log"), mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

dir_ods = os.path.join(os.path.dirname(__file__), "data", "ods")
archivo_salida = os.path.join(os.path.dirname(__file__), "data", "trafico_valencia.parquet")

def extraer_mes(hoja):
    """Mapea nombres de hojas a formato MM (01-12)"""
    hoja = hoja.lower().strip()
    meses = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
    }
    # Buscar coincidencia en diccionario
    for k, v in meses.items():
        if k in hoja:
            return v
    # Buscar números (1-12)
    match = re.search(r'(\d{1,2})', hoja)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 12:
            return str(num).zfill(2)
    return None

def procesar_imds():
    ficheros = glob.glob(os.path.join(dir_ods, "*.ods"))
    lista_acumulada = []

    for f in ficheros:
        nombre_fichero = os.path.basename(f)
        logger.info(f"--- Procesando: {nombre_fichero} ---")
        
        # Extraer el año del nombre del archivo (ej: 2016)
        anio_match = re.search(r'(\d{4})', nombre_fichero)
        anio_doc = anio_match.group(1) if anio_match else "0000"

        try:
            # Leemos todas las hojas del libro
            # Usamos engine="calamine" para eficiencia
            dict_dfs = pd.read_excel(f, engine="calamine", sheet_name=None)
            logger.info(f"Hojas encontradas: {list(dict_dfs.keys())}")
        except Exception as e:
            logger.error(f"Error leyendo fichero {nombre_fichero}: {e}")
            continue
        for sheet_name, df in dict_dfs.items():
            df.columns = df.columns.astype(str).str.strip()
            # Normalizar columnas identificadoras: Renombrar 'Nombre' a 'ATA' si es necesario
            if 'ATA' not in df.columns:
                # Buscar alternativas como 'Nombre'
                at_alt = [c for c in df.columns if c.lower() == 'nombre']
                if at_alt:
                    df = df.rename(columns={at_alt[0]: 'ATA'})

            # No necesitamos normalizar DESCRIPCION ya que no se guardará

            # 2. Identificar columnas de datos (meses o IMD general)
            # Formato antiguo: tramos_imd 2016-01.IMD
            cols_meses = [c for c in df.columns if '.IMD' in c and '-' in c]
            
            # Formato nuevo: 'IMD Laborables', 'IMD Lab.', 'Lab.', etc.
            cols_generales = [c for c in df.columns if ('IMD' in c.upper() or 'LAB.' in c.upper()) and '-' not in c]

            if cols_meses:
                # Caso archivos viejos (<2019): unión por meses en columnas dentro de una hoja
                logger.info(f"  [Formato Antiguo] Meses en columnas -> Hoja: {sheet_name}")
                df_largo = df.melt(
                    id_vars=['ATA'],
                    value_vars=cols_meses,
                    var_name='FECHA_RAW',
                    value_name='IMD'
                )
                df_largo['FECHA'] = df_largo['FECHA_RAW'].str.extract(r'(\d{4}-\d{2})')
                lista_acumulada.append(df_largo)
                break 
            
            elif cols_generales:
                # Caso archivos nuevos (>=2019): una hoja por cada mes
                mes = extraer_mes(sheet_name)
                if not mes:
                    if len(dict_dfs) > 1:
                        logger.debug(f"  Saltando hoja '{sheet_name}' (no identificada como mes)")
                        continue
                    else:
                        mes = "01"

                logger.info(f"  [Formato Nuevo] Procesando hoja: {sheet_name} -> {anio_doc}-{mes}")
                
                # Identificar columnas disponibles
                has_ata = 'ATA' in df.columns
                col_valor = cols_generales[0]

                if not has_ata:
                    logger.warning(f"  ⚠️ Hoja '{sheet_name}' NO TIENE columna 'ATA' o 'Nombre'. Columnas: {list(df.columns)}")
                    continue
                
                df_largo = df.copy()
                df_largo = df_largo.rename(columns={col_valor: 'IMD'})
                df_largo['FECHA'] = f"{anio_doc}-{mes}"
                
                # Seleccionar solo lo necesario
                df_largo = df_largo[['ATA', 'IMD', 'FECHA']]
                lista_acumulada.append(df_largo)

    if lista_acumulada:
        df_final = pd.concat(lista_acumulada, ignore_index=True)
        # Limpieza inicial
        num_antes = len(df_final)
        df_final = df_final.dropna(subset=['ATA'])
        num_despues = len(df_final)
        
        logger.info(f"Registros eliminados por ATA nulo: {num_antes - num_despues}")

        # Limpieza final de nulos, tipos y duplicados
        df_final['IMD'] = pd.to_numeric(df_final['IMD'], errors='coerce').fillna(0)
        
        # --- LOGS DE CALIDAD ---
        logger.info("=== RESUMEN DE CALIDAD DE DATOS ===")
        logger.info(f"Total registros finales: {len(df_final)}")
        logger.info(f"Rango de FECHA: {df_final['FECHA'].min()} a {df_final['FECHA'].max()}")
        logger.info(f"IMD medio: {df_final['IMD'].mean():.2f}")
        logger.info(f"IMD máximo: {df_final['IMD'].max()}")
        logger.info(f"Registros con IMD = 0: {len(df_final[df_final['IMD'] == 0])}")
        
        # Verificar si hay meses faltantes (opcional, pero útil)
        meses_unicos = df_final['FECHA'].unique()
        logger.info(f"Número de meses únicos procesados: {len(meses_unicos)}")
        
        df_final.to_parquet(archivo_salida, index=False)
        logger.info(f"✅ Datos guardados en: {archivo_salida}")
    else:
        logger.error("❌ No se encontraron datos válidos para procesar.")

if __name__ == "__main__":
    procesar_imds()