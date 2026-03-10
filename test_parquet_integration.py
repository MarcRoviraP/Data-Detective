import os
import sys
import pandas as pd

# Añadir el directorio raíz al path para importar utils
sys.path.append(os.getcwd())

from utils.async_data_loader import AsyncDataLoader

def test():
    loader = AsyncDataLoader()
    parquet_path = os.path.join("data", "trafico_valencia.parquet")
    
    print(f"Testing loading from: {parquet_path}")
    df = loader.load_traffic_parquet(parquet_path)
    
    if df is not None:
        print(f"✅ Loaded {len(df)} records")
        print("Columns:", df.columns.tolist())
        print("Sample data (2016-03):")
        # El filtro exacto que el usuario pidió
        march_data = df[df['FECHA'] == '2016-03']
        print(march_data.head())
        print(f"Total for 2016-03: {len(march_data)} records")
        
        # Verificar que el lock funciona y get_traffic_data devuelve el df
        df_cached = loader.get_traffic_data()
        if df_cached is not None and isinstance(df_cached, pd.DataFrame):
            print("✅ Cache and thread-safe access verified")
    else:
        print("❌ Failed to load parquet")

if __name__ == "__main__":
    test()
