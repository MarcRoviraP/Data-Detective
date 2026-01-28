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


class RightPanel(ft.Container):
    """
    Panel lateral derecho con archivo histórico y datos consolidados.
    Maneja la visualización de estadísticas históricas y navegación por fechas.
    """

    def __init__(self, page: ft.Page):
        print("🔧 Inicializando RightPanel...")
        super().__init__()
        self._page = page
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
            "rain": {"year_start": 2000, "year_end": 2026, "month_start": 1, "month_end": 1},
            "traffic": {"year_start": 2000, "year_end": 2026, "month_start": 1, "month_end": 1}
        }

        # Datos históricos de contaminación (indexados por año-mes)
        self.indexed_data = {}
        self.pollution_markers = []

        self.content = ft.Container(

            padding=10,
            content=ft.Column(

                controls=[
                    ft.Text("DATOS HISTORICOS"),
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
                                value="11",  # Valor por defecto
                            ),
                            ft.Dropdown(
                                ref=self.year_dropdown_ref,
                                options=[ft.dropdown.Option(str(i))
                                         for i in range(1994, 2027)],
                                width=120,
                                dense=True,
                                hint_text="Año",
                                value="2025",  # Valor por defecto
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

                    # Título del mapa
                    ft.Text("Ubicación de Sensores", size=14,
                            weight=ft.FontWeight.BOLD),

                    # Mapa
                    ft.Container(
                        content=self._create_mini_map(),
                        expand=True,
                    )
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ))
        # Cargar datos históricos
        self.load_historical_pollution_data()

        # Inicializar rangos de fecha para la capa por defecto (pollution)
        self.update_date_ranges_for_layer(self.current_layer)
        # Trigger initial update para mostrar los marcadores por defecto
        if self.current_layer == "pollution":
            self.update_pollution_markers()

        print("✅ RightPanel inicializado correctamente")

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

        # Actualizar marcadores según la capa
        if self.current_layer == "pollution":
            self.update_pollution_markers()

        self._page.update()

    def _create_mini_map(self):
        """Crea un mapa simplificado para el panel derecho."""
        return mapa.Map(
            ref=self.map_ref,
            width=400,
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

    def load_historical_pollution_data(self):
        """Carga metadata de datos históricos (JSON fragmentado por año)."""
        # Inicializar siempre, incluso si falla la carga
        self.metadata = {}
        self.year_cache = {}
        self.json_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                           "data", "pollution_historical")

        metadata_path = os.path.join(self.json_base_path, "metadata.json")

        if not os.path.exists(metadata_path):
            print(f"❌ Archivo metadata no encontrado: {metadata_path}")
            print(
                "   ℹ️  Ejecuta utils/generate_json_indexed.py para generar los archivos JSON")
            return

        print(f"📂 Cargando metadata de datos históricos...")

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

            print(f"✅ Metadata cargada: {
                  len(self.metadata['years'])} años disponibles")
            print(f"   📅 Rango: {
                  min(self.metadata['years'])}-{max(self.metadata['years'])}")

        except Exception as e:
            print(f"❌ Error al cargar metadata: {e}")

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

                # Crear tooltip detallado
                tooltip_text = (
                    f"{sensor['nombre']}\n"
                    f"NO2: {
                        sensor['no2_avg']:.1f} μg/m³\n" if sensor['no2_avg'] else f"{sensor['nombre']}\nNO2: N/A\n"
                )
                if sensor['o3_avg']:
                    tooltip_text += f"O3: {sensor['o3_avg']:.1f} μg/m³\n"
                if sensor['pm10_avg']:
                    tooltip_text += f"PM10: {sensor['pm10_avg']:.1f} μg/m³\n"
                tooltip_text += f"Período: {month}/{year}"

                # Crear marcador
                marker = self._create_marker(
                    lat, lon, color, ft.icons.Icons.CLOUD, marker_data, tooltip_text)
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

    def _create_marker(self, lat, lon, color, icon, marker_data=None, tooltip_text=None):
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
            ),
            coordinates=mapa.MapLatitudeLongitude(lat, lon),
        )

    def on_search_click(self, e):
        """Manejador del botón de búsqueda."""
        month = self.month_dropdown_ref.current.value if self.month_dropdown_ref.current else None
        year = self.year_dropdown_ref.current.value if self.year_dropdown_ref.current else None
        print(f"\n🔍 Búsqueda solicitada: mes={month}, año={
              year}, capa={self.current_layer}")

        # Actualizar según la capa activa
        if self.current_layer == "pollution":
            print("  → Actualizando marcadores de contaminación...")
            self.update_pollution_markers()
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
