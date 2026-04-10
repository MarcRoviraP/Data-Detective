"""
Filtra los parquets de tráfico histórico al bounding box de Valencia ciudad.
Ejecutar SOLO UNA VEZ para recrear los parquets filtrados.

Bounding box:
  Norte: 39.515129527427476
  Sur:   39.430853444811085
  Oeste: -0.4164094208887753
  Este:  -0.3350419311312543
"""

import pandas as pd
import os

BASE = os.path.dirname(__file__)
COORDS_PATH = os.path.join(BASE, "data", "trafico_valencia_coords.parquet")
DATA_PATH   = os.path.join(BASE, "data", "trafico_valencia.parquet")

LAT_MAX =  39.515129527427476
LAT_MIN =  39.430853444811085
LON_MIN = -0.4164094208887753
LON_MAX = -0.3350419311312543

# ── 1. Filtrar coords por bbox ──────────────────────────────────────────────
print("📦 Leyendo trafico_valencia_coords.parquet...")
df_coords = pd.read_parquet(COORDS_PATH, engine="pyarrow")
print(f"   Total original: {len(df_coords):,} tramos")

df_coords["LAT"] = pd.to_numeric(df_coords["LAT"], errors="coerce")
df_coords["LON"] = pd.to_numeric(df_coords["LON"], errors="coerce")

df_coords_filtered = df_coords[
    df_coords["LAT"].notna() & df_coords["LON"].notna() &
    (df_coords["LAT"] >= LAT_MIN) & (df_coords["LAT"] <= LAT_MAX) &
    (df_coords["LON"] >= LON_MIN) & (df_coords["LON"] <= LON_MAX)
]
print(f"   Dentro del bbox: {len(df_coords_filtered):,} tramos "
      f"(eliminados {len(df_coords) - len(df_coords_filtered):,})")

df_coords_filtered.to_parquet(COORDS_PATH, index=False, engine="pyarrow")
print("✅ trafico_valencia_coords.parquet actualizado")

# ── 2. Filtrar datos históricos por los ATAs que quedan ──────────────────────
atas_validos = set(df_coords_filtered["ATA"].dropna().astype(str).tolist())
print(f"\n📦 Leyendo trafico_valencia.parquet...")
df_data = pd.read_parquet(DATA_PATH, engine="pyarrow")
print(f"   Total original: {len(df_data):,} registros")

df_data["ATA"] = df_data["ATA"].astype(str)
df_data_filtered = df_data[df_data["ATA"].isin(atas_validos)]
print(f"   Dentro del bbox: {len(df_data_filtered):,} registros "
      f"(eliminados {len(df_data) - len(df_data_filtered):,})")

df_data_filtered.to_parquet(DATA_PATH, index=False, engine="pyarrow")
print("✅ trafico_valencia.parquet actualizado")

print("\n🎉 Parquets filtrados correctamente. Reinicia la app.")
