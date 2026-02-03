"""
Panel lateral derecho con archivo histórico y análisis.
Reescrito para mayor robustez y manejo de estado.
"""

import flet as ft
from config.theme import COLORS
from .ui_elements import UIElements
import os
import json
import datetime

import flet_map as mapa
from config.map_styles import MAP_STYLES
from utils.async_data_loader import AsyncDataLoader


class RightPanel(ft.Container):
    """
    Panel lateral derecho con archivo histórico y datos consolidados.
    Maneja la visualización de estadísticas históricas y navegación por fechas.
    """

    def __init__(self, page: ft.Page):
        print("🔧 Inicializando RightPanel...")
        super().__init__()
        self._page = page
        self.width = 500
        self.animate = ft.Animation(
            duration=300, 
            curve=ft.AnimationCurve.EASE_IN_OUT
        )   
        self.on_hover = self.animarTamanio
    
        
        self.current_layer = "pollution"  # Default layer
        self.btnRef = ft.Ref[ft.Row]()
        self.map_ref = ft.Ref[mapa.Map]()
        self.marker_layer_ref = ft.Ref[mapa.MarkerLayer]()

        # Referencias para dropdowns
        self.month_dropdown_ref = ft.Ref[ft.Dropdown]()
        self.year_dropdown_ref = ft.Ref[ft.Dropdown]()

        # Rangos de fechas por capa
        self.date_ranges = {
            "pollution": {"year_start": 1994, "year_end": 2025, "month_start": 4, "month_end": 11},
            "rain": {"year_start": 2007, "year_end": 2024, "month_start": 1, "month_end": 12},
            "traffic": {"year_start": 2000, "year_end": 2026, "month_start": 1, "month_end": 1}
        }

        # Datos AEMET
        self.aemet_data = {}
        self.weather_markers = []
        self.weather_stations_info = {}
        self.selected_weather_station = "8414A"  # Default Valencia Aeropuerto

        # Estado de carga
        self.data_loaded = False

        self.weather_info_text = ft.Text("", size=12, color=ft.Colors.BLUE_400)
        self.weather_container = ft.Container(
            
            content=ft.Column([
                ft.Text("RESUMEN CLIMATOLÓGICO", size=14,
                        weight=ft.FontWeight.BOLD),
                self.weather_info_text
            ]),
            padding=10,
            bgcolor="#161b22",
            border_radius=10,
            visible=False,
            
        )

        self.pollution_info_text = ft.Text(
            "", size=12, color=ft.Colors.GREEN_400)
        self.pollution_container = ft.Container(
            content=ft.Column([
                ft.Text("DETALLE DE CALIDAD DEL AIRE", size=14,
                        weight=ft.FontWeight.BOLD),
                self.pollution_info_text
            ]),
            padding=10,
            bgcolor="#161b22",
            border_radius=10,
            visible=False
        )

        self.content = ft.Container(
            padding=10,
            content=ft.Column(
                controls=[
                    ft.Text("DATOS HISTORICOS", size=30,
                            weight=ft.FontWeight.BOLD),
                    # Botones de capa
                    ft.Row(
                        ref=self.btnRef,
                        controls=[
                            ft.ElevatedButton(
                                "Contaminación",
                                icon="sensors",
                                on_click=lambda _: self.update_map_layer(
                                    "pollution"),
                                bgcolor=ft.Colors.GREEN if self.current_layer == "pollution" else ft.Colors.AMBER,
                                color=ft.Colors.WHITE if self.current_layer == "pollution" else ft.Colors.BLACK,
                                expand=True
                            ),
                            ft.ElevatedButton(
                                "Precipitaciones",
                                icon="grain",
                                on_click=lambda _: self.update_map_layer(
                                    "rain"),
                                bgcolor=ft.Colors.BLUE if self.current_layer == "rain" else ft.Colors.AMBER,
                                color=ft.Colors.WHITE if self.current_layer == "rain" else ft.Colors.BLACK,
                                expand=True
                            ),
                            ft.ElevatedButton(
                                "Tráfico",
                                icon="traffic",
                                on_click=lambda _: self.update_map_layer(
                                    "traffic"),
                                bgcolor=ft.Colors.RED if self.current_layer == "traffic" else ft.Colors.AMBER,
                                color=ft.Colors.WHITE if self.current_layer == "traffic" else ft.Colors.BLACK,
                                expand=True
                            ),
                        ],
                        spacing=5,
                    ),

                    # Título + Selectores + Botón de búsqueda
                    ft.Row(
                        controls=[
                            ft.Text("Período:", size=12,
                                    weight=ft.FontWeight.BOLD),
                            ft.Dropdown(
                                ref=self.month_dropdown_ref,
                                options=[ft.dropdown.Option(
                                    str(i)) for i in range(1, 13)],
                                width=120,
                                dense=True,
                                hint_text="Mes",
                                value="11",
                            ),
                            ft.Dropdown(
                                ref=self.year_dropdown_ref,
                                options=[ft.dropdown.Option(
                                    str(i)) for i in range(1994, 2027)],
                                width=120,
                                dense=True,
                                hint_text="Año",
                                value="2025",
                            ),
                            ft.IconButton(
                                icon=ft.icons.Icons.SEARCH,
                                tooltip="Buscar datos históricos",
                                bgcolor=ft.Colors.BLUE_700,
                                icon_color=ft.Colors.WHITE,
                                on_click=lambda e: self.on_search_click(e),
                                width=40,
                                height=40,
                            ),
                        ],
                        spacing=5,
                        alignment=ft.MainAxisAlignment.START,
                    ),

                    # Resumen AEMET
                    self.weather_container,
                    self.pollution_container,
                    # Mini mapa para mostrar la ubicación del sensor seleccionado
                    ft.Text("Ubicación de Sensores", size=14,
                            weight=ft.FontWeight.BOLD),

                    # Mapa
                    ft.Container(
                        content=self._create_mini_map(),
                        expand=True,
                        
                    ),
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ))

        # Inicializar rangos de fecha para la capa por defecto (pollution)
        self.update_date_ranges_for_layer(self.current_layer)

        # Cargar datos históricos de forma asíncrona
        self.start_async_data_loading()

        print("✅ RightPanel inicializado correctamente")
    def animarTamanio(self, e):
        if self.width == 500:
            self.width = 800
        else:
            self.width = 500
        self.update() 

    def setup_event_handlers(self):
        """Configurar event handlers después de que la página esté lista."""
        print("🔧 setup_event_handlers llamado")
        print(
            "  ℹ️ Usando botón de búsqueda en su lugar (Flet no soporta on_change dinámico)")
        # Nota: Flet Dropdown no soporta asignar on_change después de la creación
        # Por eso usamos un botón de búsqueda explícito

    def update_map_layer(self, layer: str):
        """Actualiza la capa del mapa."""
        self.current_layer = layer
        self.btnRef.current.controls[0].bgcolor = ft.Colors.GREEN if self.current_layer == "pollution" else ft.Colors.AMBER
        self.btnRef.current.controls[1].bgcolor = ft.Colors.BLUE if self.current_layer == "rain" else ft.Colors.AMBER
        self.btnRef.current.controls[2].bgcolor = ft.Colors.RED if self.current_layer == "traffic" else ft.Colors.AMBER
        self.btnRef.current.controls[0].color = ft.Colors.WHITE if self.current_layer == "pollution" else ft.Colors.BLACK
        self.btnRef.current.controls[1].color = ft.Colors.WHITE if self.current_layer == "rain" else ft.Colors.BLACK
        self.btnRef.current.controls[2].color = ft.Colors.WHITE if self.current_layer == "traffic" else ft.Colors.BLACK

        # Actualizar rangos de fecha para esta capa
        self.update_date_ranges_for_layer(layer)

        # Resetear visibilidad de contenedores al cambiar capa
        self.weather_container.visible = False
        self.pollution_container.visible = False

        # Actualizar marcadores según la capa
        if self.current_layer == "pollution":
            self.update_pollution_markers()
        elif self.current_layer == "rain":
            self.update_weather_markers()

        # self.update_weather_summary()
        self._page.update()

    def _create_mini_map(self):
        """Crea un mapa simplificado para el panel derecho."""
        return mapa.Map(
            ref=self.map_ref,
            
            height=400,
            # expand=True, # Removed to avoid layout conflict
            initial_center=mapa.MapLatitudeLongitude(39.4699, -0.3763),
            initial_zoom=12,
            interaction_configuration=mapa.InteractionConfiguration(
                flags=mapa.InteractionFlag.ALL
            ),
            layers=[
                mapa.TileLayer(
                    url_template=MAP_STYLES["Normal"],
                ),
                mapa.MarkerLayer(ref=self.marker_layer_ref, markers=[]),
            ],
        )

    def start_async_data_loading(self):
        """Inicia la carga asíncrona de datos históricos."""
        # Inicializar estructuras de datos
        self.metadata = {}
        self.year_cache = {}
        self.json_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                           "data", "pollution_historical")

        # Rutas para AEMET
        aemet_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "data", "aemet_historical")
        stations_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     "utils", "valencia_stations.json")

        def on_complete(success: bool):
            print(
                f"\n{'✅' if success else '⚠️'} Carga de datos completada (éxito={success})")
            self.on_data_loaded()

        # Crear instancia del loader
        self.data_loader = AsyncDataLoader()
        self.data_loader.load_all_async(
            self.json_base_path,
            aemet_dir,
            stations_path,
            on_complete=on_complete
        )

    def on_data_loaded(self):
        """Callback cuando los datos terminan de cargar."""
        # Obtener datos cargados
        pollution_data = self.data_loader.get_pollution_data()
        aemet_data = self.data_loader.get_aemet_data()

        if pollution_data:
            self.metadata = pollution_data.get('metadata', {})
            self.year_cache = pollution_data.get('year_cache', {})

        if aemet_data:
            self.aemet_data = aemet_data.get('aemet_data', {})
            self.weather_stations_info = aemet_data.get(
                'weather_stations_info', {})

        # Marcar como cargado
        self.data_loaded = True

        # Actualizar UI con datos
        if self.current_layer == "pollution":
            self.update_pollution_markers()
            self.update_weather_summary()

        if self._page:
            self._page.update()

        print("✅ UI actualizada con datos cargados")

    def load_historical_pollution_data(self):
        """Carga metadata de datos históricos (JSON fragmentado por año)."""
        # Este método ahora es llamado por el AsyncDataLoader
        # Mantenido por compatibilidad pero no se usa directamente
        pass

    def load_year_data(self, year):
        """Carga datos de un año específico bajo demanda."""
        year = int(year)

        if year not in self.year_cache:
            json_path = os.path.join(self.json_base_path, f"{year}.json")

            if not os.path.exists(json_path):
                print(f"⚠️ Archivo no encontrado: {json_path}")
                return None

            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.year_cache[year] = json.load(f)
                print(f"📖 Año {year} cargado en caché")
            except Exception as e:
                print(f"❌ Error al cargar {year}.json: {e}")
                return None

        return self.year_cache[year]

    def filter_sensors_by_date(self, month, year):
        """Filtra sensores únicos por mes y año usando datos JSON indexados."""
        if not month or not year:
            return []

        try:
            month_str = str(int(month))
            year_int = int(year)

            # Cargar datos del año (bajo demanda, con caché)
            year_data = self.load_year_data(year_int)

            if not year_data:
                print(f"⚠️ No hay datos para el año {year}")
                return []

            # Buscar mes en los datos del año
            if month_str not in year_data['months']:
                print(f"⚠️ No hay datos para {month}/{year}")
                return []

            sensors_data = year_data['months'][month_str]
            filtered_sensors = []

            # Calcular promedios para cada sensor
            for cod_estacion, sensor in sensors_data.items():
                sensor_info = {
                    'cod': cod_estacion,
                    'nombre': sensor['nombre'],
                    'lat': sensor['lat'],
                    'lon': sensor['lon'],
                    'no2_avg': sum(sensor['no2_values']) / len(sensor['no2_values']) if sensor['no2_values'] else None,
                    'o3_avg': sum(sensor['o3_values']) / len(sensor['o3_values']) if sensor['o3_values'] else None,
                    'pm10_avg': sum(sensor['pm10_values']) / len(sensor['pm10_values']) if sensor['pm10_values'] else None,
                }
                filtered_sensors.append(sensor_info)

            print(f"🔍 Encontrados {len(filtered_sensors)
                                   } sensores para {month}/{year}")
            return filtered_sensors

        except Exception as e:
            print(f"❌ Error al filtrar sensores: {e}")
            return []

    def update_pollution_markers(self):
        """Actualiza los marcadores de contaminación según la fecha seleccionada."""
        print("\n🗺️ update_pollution_markers llamado")

        # Obtener valores de los dropdowns
        month = self.month_dropdown_ref.current.value if self.month_dropdown_ref.current else None
        year = self.year_dropdown_ref.current.value if self.year_dropdown_ref.current else None

        print(f"  Mes seleccionado: {month}")
        print(f"  Año seleccionado: {year}")

        if not month or not year:
            print("  ⚠️ No hay mes o año seleccionado")
            return

        # Filtrar sensores por fecha
        sensors = self.filter_sensors_by_date(month, year)

        # Limpiar marcadores anteriores
        self.pollution_markers = []

        # Crear nuevos marcadores
        for sensor in sensors:
            try:
                lat = float(sensor['lat'])
                lon = float(sensor['lon'])

                # Determinar color según nivel de contaminación (usando NO2 como primario)
                color = COLORS["primary"]
                if sensor['no2_avg'] is not None:
                    if sensor['no2_avg'] > 40:
                        color = COLORS["event_danger"]
                    elif sensor['no2_avg'] > 20:
                        color = COLORS["traffic"]

                # Crear datos del marcador con información detallada
                marker_data = {
                    "tipo": "contaminacion_historica",
                    "titulo": sensor['nombre'],
                    "icon": ft.icons.Icons.CLOUD,
                    "color": color,
                    "info": {
                        "Estación": sensor['nombre'],
                        "Código": sensor['cod'],
                        "NO2 Promedio": f"{sensor['no2_avg']:.1f} μg/m³" if sensor['no2_avg'] else "N/A",
                        "O3 Promedio": f"{sensor['o3_avg']:.1f} μg/m³" if sensor['o3_avg'] else "N/A",
                        "PM10 Promedio": f"{sensor['pm10_avg']:.1f} μg/m³" if sensor['pm10_avg'] else "N/A",
                        "Período": f"{month}/{year}"
                    }
                }

                # Crear tooltip simplificado (solo nombre)
                tooltip_text = sensor['nombre']

                # Crear marcador
                marker = self._create_marker(
                    lat,
                    lon,
                    color,
                    ft.icons.Icons.CLOUD,
                    marker_data,
                    tooltip_text,
                    on_click=lambda e, s=sensor: self.on_pollution_sensor_click(
                        s)
                )
                self.pollution_markers.append(marker)

            except (ValueError, TypeError) as e:
                print(f"⚠️ Error con coordenadas del sensor {
                      sensor['cod']}: {e}")
                continue

        # Actualizar capa de marcadores
        if self.marker_layer_ref.current:
            self.marker_layer_ref.current.markers = self.pollution_markers
            print(f"✅ {len(self.pollution_markers)
                       } marcadores de contaminación agregados al mapa")
            if self._page:
                self._page.update()

    def _create_marker(self, lat, lon, color, icon, marker_data=None, tooltip_text=None, on_click=None):
        """Crea un marcador para el mini-mapa."""
        # Color de fondo con transparencia
        bg_color = color + "33"

        # Usar tooltip personalizado o por defecto
        if tooltip_text is None and marker_data:
            tooltip_text = marker_data.get("titulo", "Sensor")

        return mapa.Marker(
            content=ft.Container(
                width=30,
                height=30,
                bgcolor=bg_color,
                border_radius=15,
                alignment=ft.alignment.Alignment(0, 0),
                content=ft.Icon(
                    icon,
                    color=color,
                    size=18
                ),
                tooltip=tooltip_text,
                on_click=on_click
            ),
            coordinates=mapa.MapLatitudeLongitude(lat, lon),
        )

    def _dms_to_decimal(self, dms_str):
        """Convierte coordenadas de formato AEMET (DDMMSSX) a decimal."""
        if not dms_str or len(dms_str) < 7:
            return None

        try:
            direction = dms_str[-1]
            seconds = float(dms_str[-3:-1])
            minutes = float(dms_str[-5:-3])
            degrees = float(dms_str[:-5])

            decimal = degrees + (minutes / 60) + (seconds / 3600)

            if direction in ['S', 'W']:
                decimal = -decimal

            return decimal
        except Exception as e:
            print(f"⚠️ Error convirtiendo DMS '{dms_str}': {e}")
            return None

    def load_aemet_historical_data(self):
        """Carga los datos históricos de AEMET y la información de las estaciones."""
        # Este método ahora es llamado por el AsyncDataLoader
        # Mantenido por compatibilidad pero no se usa directamente
        pass

    def update_weather_summary(self):
        """Actualiza el resumen climatológico según la fecha y estación seleccionada."""
        month = self.month_dropdown_ref.current.value if self.month_dropdown_ref.current else None
        year = self.year_dropdown_ref.current.value if self.year_dropdown_ref.current else None

        if not month or not year or not self.selected_weather_station:
            self.weather_container.visible = False
            return

        station_info = self.weather_stations_info.get(
            self.selected_weather_station, {})
        station_name = station_info.get('nombre', 'Desconocida')

        # AEMET usa formato YYYY-MM (con cero inicial si es necesario)
        month_int = int(month)
        date_key_long = f"{year}-{month_int:02}"
        date_key_short = f"{year}-{month_int}"

        station_data = self.aemet_data.get(self.selected_weather_station, {})
        weather = station_data.get(
            date_key_long) or station_data.get(date_key_short)

        if weather:
            tm_mes = weather.get('tm_mes', 'N/A')
            p_mes = weather.get('p_mes', 'N/A')
            tm_max = weather.get('tm_max', 'N/A')
            tm_min = weather.get('tm_min', 'N/A')

            self.weather_container.content.controls[0].value = f"RESUMEN CLIMATOLÓGICO: {
                station_name}"
            self.weather_info_text.value = (
                f"🌡️ Temp. Media: {tm_mes}°C\n"
                f"📈 Temp. Máx: {tm_max}°C | 📉 Mín: {tm_min}°C\n"
                f"🌧️ Precipitación: {p_mes} mm"
            )
            self.weather_container.visible = True
        else:
            self.weather_container.visible = False

        if self._page:
            self._page.update()

    def update_weather_markers(self):
        """Actualiza los marcadores de estaciones meteorológicas."""
        print("\n🌧️ update_weather_markers llamado")

        self.weather_markers = []

        for indicativo, info in self.weather_stations_info.items():
            if not info['lat'] or not info['lon']:
                continue

            color = ft.Colors.BLUE if indicativo == self.selected_weather_station else ft.Colors.BLUE_200

            marker_data = {
                "tipo": "clima_historico",
                "indicativo": indicativo,
                "titulo": info['nombre']
            }

            tooltip = f"Estación: {info['nombre']}"
            if indicativo == self.selected_weather_station:
                tooltip += " (Seleccionada)"

            # Crear marcador interactivo
            marker_content = ft.Container(
                width=30,
                height=30,
                bgcolor=color + "33",
                border_radius=15,
                alignment=ft.alignment.Alignment(0, 0),
                content=ft.Icon(
                    ft.icons.Icons.GRAIN,
                    color=color,
                    size=18
                ),
                tooltip=tooltip,
                on_click=lambda e, ind=indicativo: self.on_weather_station_click(
                    ind)
            )

            marker = mapa.Marker(
                content=marker_content,
                coordinates=mapa.MapLatitudeLongitude(
                    info['lat'], info['lon']),
            )
            self.weather_markers.append(marker)

        if self.marker_layer_ref.current:
            self.marker_layer_ref.current.markers = self.weather_markers
            print(f"✅ {len(self.weather_markers)
                       } marcadores meteorológicos agregados")
            if self._page:
                self._page.update()

    def on_weather_station_click(self, indicativo):
        """Manejador al hacer clic en una estación meteorológica."""
        print(f"📍 Estación seleccionada: {indicativo}")
        self.selected_weather_station = indicativo
        self.update_weather_markers()
        self.update_weather_summary()

    def on_pollution_sensor_click(self, sensor):
        """Manejador al hacer clic en un sensor de contaminación."""
        print(f"📍 Sensor seleccionado: {sensor['nombre']}")

        no2 = sensor.get('no2_avg')
        o3 = sensor.get('o3_avg')
        pm10 = sensor.get('pm10_avg')

        info_text = (
            f"📍 Estación: {sensor['nombre']}\n"
            f"💨 NO2: {no2:.1f} μg/m³\n" if no2 else "💨 NO2: N/A\n"
        )
        if o3:
            info_text += f"🌬️ O3: {o3:.1f} μg/m³\n"
        if pm10:
            info_text += f"🌑 PM10: {pm10:.1f} μg/m³\n"

        self.pollution_info_text.value = info_text
        self.pollution_container.visible = True

        # Opcional: Centrar el mini-mapa en el sensor
        if self.map_ref.current:
            self.map_ref.current.center = mapa.MapLatitudeLongitude(
                float(sensor['lat']), float(sensor['lon']))
            self.map_ref.current.zoom = 13

        if self._page:
            self._page.update()

    def on_search_click(self, e):
        """Manejador del botón de búsqueda."""
        month = self.month_dropdown_ref.current.value if self.month_dropdown_ref.current else None
        year = self.year_dropdown_ref.current.value if self.year_dropdown_ref.current else None
        print(f"\n🔍 Búsqueda solicitada: mes={month}, año={
              year}, capa={self.current_layer}")

        # Actualizar resumen climatológico independientemente de la capa
        # self.update_weather_summary()

        # Actualizar según la capa activa
        if self.current_layer == "pollution":
            print("  → Actualizando marcadores de contaminación...")
            self.update_pollution_markers()
        elif self.current_layer == "rain":
            print("  → Actualizando marcadores meteorológicos...")
            self.update_weather_markers()
        else:
            print(f"  ⚠️ Capa '{
                  self.current_layer}' no soporta búsqueda histórica aún")

    def on_year_change(self, e):
        """Manejador cuando cambia el año - actualiza los meses disponibles."""
        print(f"\n🔄 on_year_change llamado: año={
              e.control.value if e and e.control else 'N/A'}")
        # Actualizar rangos de mes según el año seleccionado
        self.update_date_ranges_for_layer(self.current_layer)
        # Luego actualizar los marcadores
        self.on_date_change(e)

    def on_date_change(self, e):
        """Manejador de cambio de fecha en los dropdowns."""
        month = self.month_dropdown_ref.current.value if self.month_dropdown_ref.current else None
        year = self.year_dropdown_ref.current.value if self.year_dropdown_ref.current else None
        print(f"\n📅 on_date_change llamado: mes={
              month}, año={year}, capa={self.current_layer}")

        # Auto-actualizar según la capa activa
        if self.current_layer == "pollution":
            print("  → Actualizando marcadores de contaminación...")
            self.update_pollution_markers()
        else:
            print(f"  ⚠️ Capa '{
                  self.current_layer}' no soporta auto-actualización aún")
        # Para las otras capas, podrías agregar lógica similar aquí

    def update_date_ranges_for_layer(self, layer: str):
        """Actualiza los rangos de fechas disponibles según la capa seleccionada."""
        if layer not in self.date_ranges:
            return

        range_config = self.date_ranges[layer]

        # Guardar valores actuales antes de actualizar opciones
        current_month = self.month_dropdown_ref.current.value if self.month_dropdown_ref.current else None
        current_year = self.year_dropdown_ref.current.value if self.year_dropdown_ref.current else None

        # Actualizar opciones de año
        if self.year_dropdown_ref.current:
            year_options = []
            for year in range(range_config["year_start"], range_config["year_end"] + 1):
                year_options.append(ft.dropdown.Option(str(year)))

            self.year_dropdown_ref.current.options = year_options

            # Mantener valor actual si está en rango, si no usar el último
            if current_year and int(current_year) >= range_config["year_start"] and int(current_year) <= range_config["year_end"]:
                self.year_dropdown_ref.current.value = current_year
            else:
                self.year_dropdown_ref.current.value = str(
                    range_config["year_end"])

        # Actualizar opciones de mes
        if self.month_dropdown_ref.current:
            # Usar el año seleccionado actual para determinar meses disponibles
            selected_year = self.year_dropdown_ref.current.value if self.year_dropdown_ref.current else None

            month_options = []
            if selected_year == str(range_config["year_end"]):
                # Si es el último año, solo mostrar meses hasta month_end
                for month in range(1, range_config["month_end"] + 1):
                    month_options.append(ft.dropdown.Option(str(month)))
                # Mantener valor actual si está en rango
                if current_month and int(current_month) <= range_config["month_end"]:
                    self.month_dropdown_ref.current.value = current_month
                else:
                    self.month_dropdown_ref.current.value = str(
                        range_config["month_end"])
            elif selected_year == str(range_config["year_start"]):
                # Si es el primer año, solo mostrar meses desde month_start
                for month in range(range_config["month_start"], 13):
                    month_options.append(ft.dropdown.Option(str(month)))
                # Mantener valor actual si está en rango
                if current_month and int(current_month) >= range_config["month_start"]:
                    self.month_dropdown_ref.current.value = current_month
                else:
                    self.month_dropdown_ref.current.value = str(
                        range_config["month_start"])
            else:
                # Año intermedio, mostrar todos los meses
                for month in range(1, 13):
                    month_options.append(ft.dropdown.Option(str(month)))
                # Mantener valor actual
                if current_month:
                    self.month_dropdown_ref.current.value = current_month
                else:
                    self.month_dropdown_ref.current.value = "1"

            self.month_dropdown_ref.current.options = month_options

        if self._page:
            self._page.update()
