# 🔧 Posibles Mejoras — Data Detective

Documento de referencia con las áreas identificadas donde el proyecto puede crecer en calidad, rendimiento y funcionalidad.

---

## 🗄️ 1. Datos e integración

### 1.1 Actualización periódica en tiempo real
- **Problema actual**: los datos de tiempo real (tráfico, calidad del aire, meteorología) solo se cargan una vez al arrancar la aplicación.
- **Mejora**: implementar un `ScheduledRefresher` basado en `threading.Timer` o `asyncio` que renueve los datos cada N minutos sin reiniciar la app, y actualice los marcadores del mapa automáticamente.

### 1.2 Caché persistente de datos RT
- **Problema actual**: `data_service.py` guarda los datos en memoria; al cerrar la app se pierden.  
- **Mejora**: serializar la caché a disco (JSON / SQLite) con TTL configurable para evitar peticiones redundantes entre sesiones cercanas.

### 1.3 Ampliar fuentes de contaminación
- El histórico de la GVA solo incluye NO₂, O₃ y PM10; faltan contaminantes como **SO₂, CO y PM2.5**.  
- Explorar el dataset de [EEA (European Environment Agency)](https://www.eea.europa.eu/data-and-maps/data/aqereporting-9) como fuente complementaria.

### 1.4 Histórico de tráfico más rico
- El `trafico_valencia.parquet` actual es un archivo estático.  
- **Mejora**: programar un descargador periódico que acumule snapshot diarios de la API RT para construir el histórico de manera continua.

### 1.5 Datos meteorológicos de AVAMET con coordenadas completas
- `avamet_coordinates.py` es una tabla estática manual con un subconjunto de estaciones.  
- **Mejora**: obtener las coordenadas directamente del XML/JSON que AVAMET publica por estación, eliminando la necesidad de mantenimiento manual.

### 1.6 Soporte para más ciudades
- La aplicación está hardcodeada para Valencia (bounding box fijo, URLs específicas).  
- **Mejora**: parametrizar la ciudad en un archivo de configuración YAML para poder replicar la plataforma en otras ciudades con portales Open Data.

---

## 🖥️ 2. Interfaz de usuario (UI/UX)

### 2.1 Gráficas históricas interactivas
- **Problema actual**: el panel derecho muestra datos textuales pero carece de gráficas de tendencia temporal.  
- **Mejora**: integrar **Flet Charts** o exportar SVG con **Matplotlib** para mostrar series temporales de NO₂, temperatura o intensidad de tráfico al seleccionar un sensor.

### 2.2 Filtros en el panel derecho
- Añadir filtros por **estación**, **rango de fechas** (además del mes/año actual) y **umbral de contaminante** para facilitar el análisis comparativo.

### 2.3 Modo responsive / pantallas pequeñas
- El layout actual asume ventana maximizada; en pantallas pequeñas los paneles se solapan o quedan cortados.  
- **Mejora**: detectar el tamaño de la ventana y colapsar/ocultar paneles laterales automáticamente.

### 2.4 Panel resizable mediante drag
- El `animarTamanio` actual alterna entre dos anchos fijos (500 / 800 px).  
- **Mejora**: permitir redimensionado libre del panel derecho arrastrando el borde.

### 2.5 Tooltip enriquecido en los marcadores
- Los tooltips muestran solo el nombre de la estación.  
- **Mejora**: mostrar el valor principal (ej. NO₂ actual o estado del tráfico) directamente en el tooltip para evitar tener que hacer clic en cada marcador.

### 2.6 Leyenda de colores en el mapa
- No existe una referencia visual que explique qué significan los colores (verde/amarillo/rojo) por tipo de capa.  
- **Mejora**: añadir una leyenda flotante dinámica que cambie según la capa activa.

### 2.7 Exportación de datos
- **Mejora**: botón para exportar los datos filtrados del panel derecho a **CSV o PDF** para uso académico o profesional.

---

## 🏛️ 3. Arquitectura y código

### 3.1 Separar la lógica de negocio de la UI
- Actualmente `right_panel.py` (≈1 234 líneas) mezcla UI, lógica de filtrado y acceso a datos.  
- **Mejora**: extraer la lógica de filtrado y las llamadas a los loaders a clases `ViewModel` o `Controller` independientes, siguiendo un patrón MVC/MVVM.

### 3.2 Eliminar `bare except` y mejorar el manejo de errores
- Hay múltiples bloques `except:` sin tipo específico (ej. en `left_panel.py` y `map_container.py`) que silencian errores inesperados.  
- **Mejora**: capturar excepciones concretas (`ValueError`, `KeyError`, `requests.Timeout`, etc.) y propagar o loguear de forma adecuada.

### 3.3 Sistema de logging estructurado
- El logging actual usa `print()` con emojis.  
- **Mejora**: sustituir por el módulo estándar `logging` de Python con niveles (`DEBUG`, `INFO`, `WARNING`, `ERROR`) y rotación de archivos de log.

### 3.4 Configuración externalizada
- Las constantes (URLs de API, bounding box, rutas de datos, TTL de caché) están dispersas en múltiples archivos.  
- **Mejora**: centralizar en un archivo `config/settings.py` o `config.yaml` con soporte para variables de entorno (`.env` + `python-dotenv`).

### 3.5 API Key de AEMET fuera del código
- Actualmente la clave de AEMET puede estar hardcodeada en scripts de descarga.  
- **Mejora**: leer la API key exclusivamente de una variable de entorno `AEMET_API_KEY` y documentar cómo configurarla.

### 3.6 Tipado estático
- Muchas funciones carecen de type hints completos.  
- **Mejora**: completar las anotaciones y ejecutar `mypy` en CI para detectar errores de tipo antes de ejecutar.

---

## 🧪 4. Testing

### 4.1 Tests unitarios de los servicios de datos
- Solo existe `test_parquet_integration.py` y algunos scripts de prueba ad-hoc.  
- **Mejora**: añadir tests con `pytest` que validen `get_air_quality_data()`, `get_traffic_data()`, `get_weather_data()` usando mocks de `requests` (librería `responses` o `unittest.mock`).

### 4.2 Tests de integración del pipeline histórico
- Validar que el ciclo completo (descarga CSV → `generate_json_indexed` → `AsyncDataLoader` → `filter_sensors_by_date`) funciona correctamente con datos sintéticos.

### 4.3 Cobertura mínima de código
- Definir un umbral de cobertura (p. ej. 70 %) e integrarlo en un flujo CI/CD (GitHub Actions).

---

## 🚀 5. Despliegue y distribución

### 5.1 Empaquetado como ejecutable
- **Mejora**: usar `flet build` (o `PyInstaller` como alternativa) para generar un `.exe` (Windows), `.app` (macOS) o AppImage (Linux) que no requiera Python instalado.

### 5.2 Docker para desarrollo reproducible
- Añadir un `Dockerfile` con todas las dependencias para facilitar la contribución de nuevos desarrolladores sin conflictos de entorno.

### 5.3 Versionado semántico y CHANGELOG
- Adoptar [Semantic Versioning](https://semver.org/) y mantener un `CHANGELOG.md` con las novedades de cada versión.

### 5.4 Modo web / PWA
- Flet soporta despliegue en modo web.  
- **Mejora**: explorar `flet publish` para ofrecer la plataforma como aplicación web accesible desde el navegador, ampliando el alcance sin necesidad de instalación local.

---

## 🔒 6. Seguridad y privacidad

### 6.1 Validación de respuestas de API
- Las respuestas JSON de las APIs externas se consumen sin validar el esquema.  
- **Mejora**: usar `pydantic` para definir modelos de datos y validar las respuestas antes de procesarlas.

### 6.2 Manejo de timeouts y reintentos
- Las peticiones `requests` tienen timeout fijo pero no reintentos automáticos ante fallos transitorios.  
- **Mejora**: usar `requests.adapters.HTTPAdapter` con `Retry` para reintentos exponenciales.

### 6.3 `.gitignore` para la API Key y datos sensibles
- Asegurarse de que ningún archivo con API keys ni los datos descargados de gran tamaño (`data/pollution_historical/*.json`, `data/trafico_valencia.parquet`) se suban al repositorio accidentalmente.  
- **Mejora**: revisar el `.gitignore` actual y añadir las rutas necesarias.

---

> 📅 Documento generado el 21 de marzo de 2026. Las prioridades pueden cambiar según los objetivos del proyecto.
