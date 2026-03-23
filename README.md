# 🕵️‍♂️ Data Detective — Valencia Urban Intel

**Data Detective** es una plataforma de escritorio interactiva para la visualización y análisis de datos urbanos de Valencia. Combina datos **en tiempo real** y **series históricas** de calidad del aire, meteorología y tráfico en una interfaz unificada y geoespacial construida 100 % en Python.

---

## 📋 Índice

1. [Arquitectura general](#-arquitectura-general)
2. [Estructura del proyecto](#-estructura-del-proyecto)
3. [Librerías utilizadas](#-librerías-utilizadas)
4. [Fuentes de datos](#-fuentes-de-datos)
   - [Datos históricos](#-datos-históricos)
   - [Datos en tiempo real](#-datos-en-tiempo-real)
5. [Instalación y ejecución](#-instalación-y-ejecución)
6. [Primera ejecución](#-primera-ejecución)

---

## 🏗 Arquitectura general

```
main.py  ──▶  DataDetectiveUI
               ├── LeftPanel      (selección de capa activa + nodos destacados)
               ├── MapContainer   (mapa interactivo central con marcadores)
               └── RightPanel     (histórico, mini-mapa, gráficas y detalle)
```

El arranque sigue este flujo:

1. **Splash screen** – verifica que los datos históricos JSON estén generados.
2. Si faltan, lanza automáticamente la descarga/conversión (`data_verifier.py`).
3. Pre-carga las tres APIs en paralelo (hilos independientes).
4. Monta la UI principal y llama a `setup_event_handlers()`.

---

## 📁 Estructura del proyecto

```
Data-Detective/
├── main.py                          # Punto de entrada
├── requeriments.txt                 # Dependencias pip
│
├── components/                      # Componentes de la UI (Flet)
│   ├── left_panel.py                # Panel izq.: selector de capas y nodos
│   ├── map_container.py             # Mapa central con marcadores en tiempo real
│   ├── right_panel.py               # Panel der.: análisis histórico y mini-mapa
│   └── ui_elements.py               # Elementos visuales reutilizables
│
├── config/                          # Configuración global
│   ├── theme.py                     # Paleta de colores COLORS
│   └── map_styles.py                # URLs de estilos de teselas (OSM, Satélite…)
│
├── utils/                           # Lógica de datos y servicios
│   ├── async_data_loader.py         # Carga paralela de históricos (threading)
│   ├── data_verifier.py             # Verifica/genera datos al iniciar
│   ├── data_service.py              # Caché y acceso unificado a datos RT
│   ├── historical_data_processor.py # Procesado de CSV de contaminación
│   ├── generate_json_indexed.py     # Convierte CSV → JSON indexado por año/mes
│   ├── optimized_data_downloader.py # Descarga los CSVs y los convierte a JSON
│   ├── consolidate_historical_data.py# Consolida múltiples fuentes históricas
│   ├── normalizerODS.py             # Normaliza archivos ODS de la GVA
│   │
│   ├── RealTimeTrafficValencia.py   # API RT: tráfico Valencia Open Data
│   ├── RealTimeAirValencia.py       # API RT: calidad del aire Valencia OD
│   ├── RealTimeValencianWeather.py  # Scraping RT: meteorología AVAMET
│   │
│   ├── AEMETDataService.py          # Cliente AEMET OpenData (con auth)
│   ├── AEMET_downloader.py          # Descarga series AEMET por estación
│   ├── GetContaminacio.py           # Descarga CSVs históricos GVA CKAN
│   ├── avamet_coordinates.py        # Mapeo nombre-estación → coordenadas GPS
│   ├── find_valencia_stations.py    # Filtra estaciones dentro de Valencia
│   └── valencia_stations.json       # Inventario de estaciones AEMET de Valencia
│
├── data/                            # Datos almacenados localmente
│   ├── pollution_historical/        # JSONs indexados de contaminación (1994-2025)
│   ├── aemet_historical/            # JSONs mensuales por estación AEMET
│   ├── trafico_valencia.parquet     # Histórico de tráfico (formato Parquet)
│   └── ods/                         # Archivos ODS fuente descargados
│
└── assets/                          # Recursos estáticos (iconos, imágenes)
```

---

## 📦 Librerías utilizadas

| Librería | Versión aprox. | Propósito |
|---|---|---|
| **flet** | ≥ 0.25 | Framework UI (Flutter/Python) – toda la interfaz gráfica |
| **flet-map** | ≥ 0.1 | Mapa interactivo con teselas OSM y marcadores |
| **requests** | ≥ 2.31 | Llamadas HTTP a todas las APIs y scraping |
| **beautifulsoup4** | ≥ 4.12 | Parseo HTML para scraping de AVAMET |
| **pandas** | ≥ 2.0 | Procesado de CSV y lectura de archivos Parquet |
| **pyarrow** | ≥ 14.0 | Motor de lectura de archivos `.parquet` |
| **lxml** | ≥ 4.9 | Parser XML/HTML alternativo para BeautifulSoup |

> Instala todas las dependencias con: `pip install -r requeriments.txt`

---

## 📊 Fuentes de datos

### 📂 Datos históricos

Datos con cobertura temporal extensa, almacenados localmente para consulta sin latencia.

---

#### 🏭 Contaminación atmosférica histórica (1994 – 2025)

- **Fuente**: [Dades Obertes GVA – CKAN](https://dadesobertes.gva.es/)
- **Dataset**: Contaminantes atmosféricos (NO₂, O₃, PM10) de estaciones de la Generalitat Valenciana.
- **Obtención**:
  1. `GetContaminacio.py` consulta la API CKAN para obtener la URL del CSV mensual.
  2. `optimized_data_downloader.py` descarga los CSVs y los convierte directamente a JSON.
  3. `generate_json_indexed.py` fragmenta un CSV consolidado en JSONs por año (`data/pollution_historical/YYYY.json`).
- **Formato local**: JSON indexado por año → mes → estación, con arrays de valores de NO₂, O₃ y PM10.
- **Módulo de procesado**: `HistoricalDataProcessor` en `utils/historical_data_processor.py`.

---

#### 🌦️ Climatología histórica AEMET (2007 – 2024)

- **Fuente**: [AEMET OpenData](https://opendata.aemet.es/) — requiere **API Key gratuita**.
- **Datos**: Resúmenes mensuales de temperatura, precipitación, viento y presión de estaciones meteorológicas oficiales dentro de Valencia ciudad.
- **Obtención**:
  1. `AEMETDataService.py` gestiona el doble paso (endpoint → URL de datos) y los límites de 36 meses por bloque.
  2. `AEMET_downloader.py` itera por estaciones y rangos de años, guardando archivos `monthly_<ID>_<rango>.json`.
  3. `find_valencia_stations.py` filtra el inventario a las estaciones dentro del bounding box de Valencia.
- **Formato local**: `data/aemet_historical/monthly_<indicativo>_<año_ini>_<año_fin>.json`
- **Estaciones cargadas**: Filtradas al bounding box `[39.40–39.55 N, 0.55–0.25 O]`.

---

#### 🚗 Tráfico histórico (2016 – 2026)

- **Fuente**: Datos municipales de aforos de tráfico de Valencia.
- **Datos**: Intensidad, ocupación, velocidad y estado por tramo/estación.
- **Obtención**: Archivo **Parquet** precompilado (`data/trafico_valencia.parquet`), leído con `pandas` + `pyarrow`.
- **Módulo de carga**: `AsyncDataLoader.load_traffic_parquet()` en `utils/async_data_loader.py`.
- **Nota**: El histórico de tráfico se carga íntegro en memoria al arrancar la app y se filtra en el panel derecho por mes/año seleccionado.

---

### 🌐 Datos en tiempo real

Datos recuperados en cada arranque de la aplicación (y susceptibles de actualización periódica).

---

#### ☁️ Calidad del aire en tiempo real

- **Fuente**: [Valencia Open Data (Opendatasoft API v2.1)](https://valencia.opendatasoft.com/)
- **Dataset**: `estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas`
- **Datos**: NO₂, PM10, O₃, calidad ambiental y coordenadas GPS por estación.
- **Módulo**: `utils/RealTimeAirValencia.py` → `get_air_quality_data()`
- **Formato de respuesta**: JSON; cada registro devuelve un objeto `EstacionContaminacionAtmosferica`.

---

#### 🚦 Tráfico en tiempo real

- **Fuente**: [Valencia Open Data (Opendatasoft API v2.1)](https://valencia.opendatasoft.com/)
- **Dataset**: `estat-transit-temps-real-estado-trafico-tiempo-real`
- **Datos**: Estado del tramo (0-9), intensidad (veh/h), ocupación (%), carga, velocidad (km/h) y coordenadas.
- **Módulo**: `utils/RealTimeTrafficValencia.py` → `get_traffic_data()`
- **Decodificador de estados**: `get_estado_descripcion()` traduce el código numérico a texto descriptivo y color (`green`/`yellow`/`red`/`gray`).

---

#### 🌧️ Meteorología en tiempo real (AVAMET)

- **Fuente**: [AVAMET – Associació Valenciana de Meteorologia](https://www.avamet.org/mx-meteoxarxa.php?territori=c15)
- **Método**: **Web scraping** con `requests` + `BeautifulSoup` (parseo de tabla HTML `.tDades`).
- **Datos**: Temperatura mín/med/máx, humedad relativa, precipitación, velocidad y dirección del viento de la red MeteoXarxa (comarca de Valencia).
- **Módulo**: `utils/RealTimeValencianWeather.py` → `get_weather_data()`
- **Coordenadas**: Resueltas con `utils/avamet_coordinates.py` (tabla estática nombre → lat/lon).

---

## 🛠️ Instalación y ejecución

### Requisitos previos

- Python 3.11 o superior
- Conexión a Internet (primera ejecución y datos RT)
- **API Key de AEMET** (gratuita) si se quieren actualizar los datos climatológicos históricos: [Regístrate aquí](https://opendata.aemet.es/centrodedescargas/altaUsuario)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/MarcRoviraP/Data-Detective.git
cd Data-Detective

# 2. (Opcional) Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Linux/macOS

# 3. Instalar dependencias
pip install -r requeriments.txt

# 4. Ejecutar la aplicación
python main.py
```

---

## 🚀 Primera ejecución

En el primer arranque, la aplicación detecta automáticamente si faltan los datos históricos de contaminación:

1. **Si no existe el CSV consolidado** → lanza una ventana de progreso y descarga ~380 archivos CSV de la GVA, convirtiéndolos directamente a JSON optimizado.
2. **Si el CSV existe pero no los JSONs** → convierte el CSV local al formato JSON indexado.
3. **Datos AEMET y Tráfico (Parquet)** → se incluyen precompilados en el repositorio; no requieren descarga adicional.

> ⚠️ La descarga inicial de datos de contaminación puede tardar **varios minutos** dependiendo de la conexión. Una vez completada, los arranques posteriores son inmediatos.
