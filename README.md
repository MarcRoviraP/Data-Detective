# 🕵️‍♂️ Data Detective - Valencia Urban Intel

**Data Detective** es una plataforma interactiva de visualización de datos en tiempo real y análisis histórico enfocada en la ciudad de Valencia. El proyecto permite monitorizar la calidad del aire, las condiciones meteorológicas y el estado del tráfico desde una interfaz unificada y moderna.

---

## 🎨 Parte Gráfica (GUI)

La interfaz ha sido desarrollada utilizando un stack tecnológico moderno centrado en Python, priorizando la interactividad y la visualización geoespacial.

### Tecnologías Principales

- **Flet**: Framework principal basado en Flutter que permite crear interfaces de usuario interactivas y reactivas directamente en Python.
- **flet-map**: Integración de mapas interactivos que permite la visualización de capas de teselas (Leaflet/OpenStreetMap) y marcadores personalizados.
- **Matplotlib / Flet Charts**: Utilizados para la generación de gráficas comparativas y análisis de tendencias históricas en el panel derecho.

### Estructura de la Interfaz

1.  **Pantalla de Carga (Splash Screen)**: Sistema de inicialización que verifica la integridad de los datos locales y pre-carga las APIs en hilos paralelos para asegurar una experiencia fluida.
2.  **Panel Izquierdo (Navegación)**: Permite conmutar entre las diferentes capas de datos:
    - 🌧️ **Precipitaciones**: Datos de lluvia en tiempo real.
    - 🌫️ **Contaminación (NO2)**: Niveles de dióxido de nitrógeno.
    - 🧪 **Contaminación (O3, PM10)**: Ozono y partículas en suspensión.
    - 🚗 **Flujo de Tráfico**: Estado de las vías principales.
3.  **Mapa Central (Visualización)**: Mapa interactivo con soporte para múltiples estilos (Normal, Satélite, Oscuro y Topográfico). Los marcadores cambian de color dinámicamente según la severidad de los datos.
4.  **Panel Derecho (Análisis)**: Panel contextual que muestra detalles específicos al seleccionar un sensor. Incluye gráficas históricas mensuales y anuales para identificar patrones.

---

## 📊 Obtención de Datos

El sistema utiliza una arquitectura de micro-servicios internos para recolectar datos de diversas fuentes oficiales, clasificados según su método de obtención:

### 🌐 1. Web Scraping (Raspado Web)

Utilizado para fuentes que no disponen de una API REST pública estructurada o que requieren una lectura directa de tablas web.

- **Fuente**: [AVAMET](https://www.avamet.org/) (Asociación Valenciana de Meteorología).
- **Datos**: Precipitaciones y temperaturas en tiempo real de la red MeteoXarxa.
- **Herramientas**: `BeautifulSoup4` para el parseo de HTML y `requests` para la navegación.

### 🔌 2. API REST (Tiempo Real)

Conexiones directas a portales de datos abiertos que ofrecen información actualizada cada pocos minutos.

- **Fuentes**:
  - [Valencia Open Data](https://valencia.opendatasoft.com/): Datos de tráfico (intensidad, ocupación, carga) y calidad del aire actual.
  - [Opendatasoft API v2.1]: Protocolo utilizado para consultas filtradas y geolocalizadas.
- **Herramientas**: Librería `requests` con manejo de formatos JSON.

### 📂 3. API REST & Descarga Automática (Histórico)

Sistemas que requieren una fase de búsqueda en catálogos y posterior descarga de volúmenes grandes de datos.

- **Fuente**: [Dades Obertes GVA](https://dadesobertes.gva.es/) (Generalitat Valenciana).
- **Datos**: Histórico de estaciones contaminantes por meses y años.
- **Método**: Consulta a la API CKAN para localizar los recursos CSV más recientes y descarga automatizada al almacenamiento local.
- **Herramientas**: `pandas` para el procesamiento de los CSV descargados y optimización a formato JSON indexado.

### 🔑 4. API REST con Autenticación (AEMET)

Acceso a servicios oficiales de alto nivel que requieren claves de API para el control de cuotas.

- **Fuente**: [AEMET OpenData](https://opendata.aemet.es/).
- **Datos**: Series históricas climatológicas de las estaciones oficiales de Valencia Ciudad.
- **Herramientas**: `AEMETDataService` (implementación propia) para la gestión de tokens y reintentos.

---

## 🛠️ Instalación y Ejecución

1.  Instalar dependencias:
    ```bash
    pip install -r requeriments.txt
    ```
2.  Ejecutar la aplicación:
    ```bash
    python main.py
    ```
    _Nota: En la primera ejecución, la aplicación descargará y procesará automáticamente los datos históricos necesarios._
