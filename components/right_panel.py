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

import pandas as pd
MONTH_NAMES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
]


class MonthYearPicker(ft.Row):
    """
    Control compacto de selección de mes y año.
    Muestra el período actual y permite navegar con flechas
    o abrir un diálogo modal con cuadrícula de meses y años.
    """

    def __init__(self, page: ft.Page,
                 initial_month: int = 1,
                 initial_year: int = 2025,
                 year_start: int = 1994,
                 year_end: int = 2025,
                 month_start: int = 1,
                 month_end: int = 12,
                 on_change=None):
        super().__init__()
        # Guardamos el estado en un dict para evitar que Flet intercepte
        # los setattr y llame a su _notify(name, value) interno.
        object.__setattr__(self, '_state', {
            'month': initial_month,
            'year': initial_year,
            'year_start': year_start,
            'year_end': year_end,
            'month_start': month_start,
            'month_end': month_end,
            'on_change_cb': on_change,
            'page': page,
        })

        # Label central clickable
        self._label_text = ft.Text(
            self._format_label(),
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.W_500,
        )
        self._label = ft.Container(
            content=self._label_text,
            bgcolor=ft.Colors.BLUE_GREY_800,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            on_click=self._open_dialog,
            ink=True,
        )

        self.controls = [
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                icon_size=18,
                tooltip="Mes anterior",
                on_click=self._prev_month,
                icon_color=ft.Colors.BLUE_300,
            ),
            self._label,
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                icon_size=18,
                tooltip="Mes siguiente",
                on_click=self._next_month,
                icon_color=ft.Colors.BLUE_300,
            ),
        ]
        self.spacing = 0
        self.vertical_alignment = ft.CrossAxisAlignment.CENTER

    # ── helpers ────────────────────────────────────────────────────────────

    @property
    def selected_month(self): return self._state['month']
    @property
    def selected_year(self): return self._state['year']
    @property
    def year_start(self): return self._state['year_start']
    @property
    def year_end(self): return self._state['year_end']
    @property
    def month_start(self): return self._state['month_start']
    @property
    def month_end(self): return self._state['month_end']

    def _set(self, **kwargs):
        """Actualiza valores del estado sin que Flet los intercepte."""
        self._state.update(kwargs)

    def _format_label(self):
        return f"{MONTH_NAMES[self._state['month'] - 1]} {self._state['year']}"

    def _refresh_label(self):
        self._label_text.value = self._format_label()
        if self._state['page']:
            self._state['page'].update()

    def _clamp_month_to_range(self):
        s = self._state
        if s['year'] == s['year_start']:
            s['month'] = max(s['month'], s['month_start'])
        if s['year'] == s['year_end']:
            s['month'] = min(s['month'], s['month_end'])

    def _fire_change(self):
        cb = self._state.get('on_change_cb')
        if cb:
            cb(self._state['month'], self._state['year'])

    # ── navigation ─────────────────────────────────────────────────────────

    def _prev_month(self, e):
        s = self._state
        m, y = s['month'] - 1, s['year']
        if m < 1:
            m, y = 12, y - 1
        if y < s['year_start'] or (y == s['year_start'] and m < s['month_start']):
            return
        self._set(month=m, year=y)
        self._refresh_label()
        self._fire_change()

    def _next_month(self, e):
        s = self._state
        m, y = s['month'] + 1, s['year']
        if m > 12:
            m, y = 1, y + 1
        if y > s['year_end'] or (y == s['year_end'] and m > s['month_end']):
            return
        self._set(month=m, year=y)
        self._refresh_label()
        self._fire_change()

    # ── modal dialog ───────────────────────────────────────────────────────

    def _open_dialog(self, e):
        """Abre el diálogo de selección de mes y año."""
        print(
            f"📅 [MonthYearPicker] _open_dialog: year={self._state['year']}, month={self._state['month']}")
        self._state['dialog_year'] = self._state['year']
        print(f"   dialog_year seteado a {self._state['dialog_year']}")
        self._build_and_show_dialog()
        print("   _build_and_show_dialog completado")

    def _build_and_show_dialog(self):
        """Construye y muestra el diálogo modal."""
        # Título con navegación de año
        year_nav = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    icon_size=18,
                    on_click=self._dialog_prev_year,
                    icon_color=ft.Colors.BLUE_300,
                ),
                ft.Text(
                    str(self._state['dialog_year']),
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    icon_size=18,
                    on_click=self._dialog_next_year,
                    icon_color=ft.Colors.BLUE_300,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Cuadrícula de meses (3 columnas × 4 filas)
        month_grid = ft.GridView(
            runs_count=3,
            max_extent=90,
            spacing=6,
            run_spacing=6,
            height=190,
        )
        self._populate_month_grid(month_grid)

        self._dialog_year_text = year_nav.controls[1]
        self._month_grid = month_grid

        page = self._state['page']
        dlg = ft.AlertDialog(
            modal=True,
            title=year_nav,
            content=ft.Container(
                content=month_grid,
                width=280,
                padding=ft.padding.symmetric(vertical=4),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1e2530",
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        object.__setattr__(self, '_active_dialog', dlg)
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _populate_month_grid(self, grid: ft.GridView):
        """Rellena la cuadrícula con botones de mes."""
        s = self._state
        dy = s['dialog_year']
        grid.controls.clear()
        for i, name in enumerate(MONTH_NAMES, start=1):
            m_num = i
            is_selected = (m_num == s['month'] and dy == s['year'])
            disabled = (
                (dy == s['year_start'] and m_num < s['month_start']) or
                (dy == s['year_end'] and m_num > s['month_end']) or
                dy < s['year_start'] or dy > s['year_end']
            )

            text_color = (
                ft.Colors.WHITE if is_selected
                else (ft.Colors.WHITE70 if not disabled else ft.Colors.BLUE_GREY_500)
            )
            bg_color = (
                ft.Colors.BLUE_700 if is_selected
                else (ft.Colors.BLUE_GREY_700 if not disabled else ft.Colors.BLUE_GREY_900)
            )
            btn = ft.Container(
                content=ft.Text(
                    name,
                    color=text_color,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_500,
                ),
                width=80,
                height=40,
                bgcolor=bg_color,
                border_radius=8,
                alignment=ft.Alignment(0, 0),
                on_click=(lambda e, m=m_num: self._select_month(m)
                          ) if not disabled else None,
                ink=not disabled,
                opacity=0.4 if disabled else 1.0,
            )
            grid.controls.append(btn)

    def _dialog_prev_year(self, e):
        s = self._state
        if s['dialog_year'] > s['year_start']:
            s['dialog_year'] -= 1
            self._dialog_year_text.value = str(s['dialog_year'])
            self._populate_month_grid(self._month_grid)
            self._state['page'].update()

    def _dialog_next_year(self, e):
        s = self._state
        if s['dialog_year'] < s['year_end']:
            s['dialog_year'] += 1
            self._dialog_year_text.value = str(s['dialog_year'])
            self._populate_month_grid(self._month_grid)
            self._state['page'].update()

    def _select_month(self, month: int):
        print(
            f"✅ [MonthYearPicker] _select_month: mes={month}, año={self._state['dialog_year']}")
        self._set(month=month, year=self._state['dialog_year'])
        self._close_dialog(None)
        self._refresh_label()
        self._fire_change()
        print(
            f"   Selección aplicada: {self._state['month']}/{self._state['year']}")

    def _close_dialog(self, e):
        page = self._state['page']
        dlg = getattr(self, '_active_dialog', None)
        if dlg is not None:
            dlg.open = False
            page.update()

    # ── public API ─────────────────────────────────────────────────────────

    @property
    def value(self):
        """Devuelve (mes, año) como tupla de strings."""
        s = self._state
        return str(s['month']), str(s['year'])

    def set_range(self, year_start, year_end, month_start, month_end):
        """Actualiza los rangos válidos y corrige la selección si es necesario."""
        s = self._state
        s['year_start'] = year_start
        s['year_end'] = year_end
        s['month_start'] = month_start
        s['month_end'] = month_end
        s['year'] = max(year_start, min(year_end, s['year']))
        self._clamp_month_to_range()
        self._refresh_label()


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

        # Date picker de mes/año
        self.period_picker = MonthYearPicker(
            page=page,
            initial_month=11,
            initial_year=2025,
            year_start=1994,
            year_end=2025,
            month_start=4,
            month_end=11,
        )

        # Rangos de fechas por capa
        self.date_ranges = {
            "pollution": {"year_start": 1994, "year_end": 2025, "month_start": 4, "month_end": 11},
            "rain": {"year_start": 2007, "year_end": 2024, "month_start": 1, "month_end": 12},
            "traffic": {"year_start": 2016, "year_end": 2026, "month_start": 1, "month_end": 1}
        }

        # Datos AEMET
        self.aemet_data = {}
        self.weather_markers = []
        self.weather_stations_info = {}
        self.selected_weather_station = "8414A"  # Default Valencia Aeropuerto
        
        # Datos Tráfico
        self.traffic_data = {}
        self.traffic_stations_info = {}
        self.traffic_markers = []
        self.selected_traffic_station = None  # Estación seleccionada en tráfico
        # self.traffic_data_df será inicializado en on_data_loaded si hay parquet
        
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

        self.traffic_info_text = ft.Text(
            "", size=12, color=ft.Colors.ORANGE_400)
        self.traffic_container = ft.Container(
            content=ft.Column([
                ft.Text("DETALLE DE TRÁFICO HISTÓRICO", size=14,
                        weight=ft.FontWeight.BOLD),
                self.traffic_info_text
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

                    # Título + Date Picker + Botón de búsqueda
                    ft.Row(
                        controls=[
                            ft.Text("Período:", size=12,
                                    weight=ft.FontWeight.BOLD),
                            self.period_picker,
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

                    # Resumen AEMET / Contaminación / Tráfico
                    self.weather_container,
                    self.pollution_container,
                    self.traffic_container,
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
        self.traffic_container.visible = False

        # Actualizar marcadores según la capa
        if self.current_layer == "pollution":
            self.update_pollution_markers()
        elif self.current_layer == "rain":
            self.update_weather_markers()
        elif self.current_layer == "traffic":
            if hasattr(self, 'traffic_data_df'):
                self.update_historical_traffic_markers()
            else:
                self.update_traffic_markers()

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
        traffic_parquet_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                            "data", "trafico_valencia.parquet")

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
            traffic_parquet_path=traffic_parquet_path,
            on_complete=on_complete
        )

    def on_data_loaded(self):
        """Callback cuando los datos terminan de cargar."""
        import traceback as _tb
    
        
        # Obtener datos cargados
        pollution_data = self.data_loader.get_pollution_data()
        aemet_data = self.data_loader.get_aemet_data()
        traffic_data = self.data_loader.get_traffic_data()

        print(f"  [on_data_loaded] tipo traffic_data: {type(traffic_data).__name__}")

        try:
            if pollution_data is not None:
                self.metadata = pollution_data.get('metadata', {})
                self.year_cache = pollution_data.get('year_cache', {})
        except Exception as e:
            print(f"❌ Error cargando pollution_data: {e}"); _tb.print_exc()

        try:
            if aemet_data is not None:
                self.aemet_data = aemet_data.get('aemet_data', {})
                self.weather_stations_info = aemet_data.get(
                    'weather_stations_info', {})
        except Exception as e:
            print(f"❌ Error cargando aemet_data: {e}"); _tb.print_exc()

        # Comprobar tráfico: puede ser DataFrame o dict; no usar bool() sobre DataFrame
        try:
            if isinstance(traffic_data, pd.DataFrame):
                self.traffic_data_df = traffic_data
                print(f"  ✅ traffic_data_df asignado: {len(self.traffic_data_df)} filas")
            elif traffic_data is not None:
                self.traffic_data = traffic_data.get('traffic_data', {})
                self.traffic_stations_info = traffic_data.get(
                    'traffic_stations_info', {})
        except Exception as e:
            print(f"❌ Error cargando traffic_data: {e}"); _tb.print_exc()

        # Marcar como cargado
        self.data_loaded = True

        # Actualizar UI con datos
        try:
            if self.current_layer == "pollution":
                self.update_pollution_markers()
                self.update_weather_summary()
        except Exception as e:
            print(f"❌ Error actualizando UI: {e}"); _tb.print_exc()

        try:
            if self._page:
                self._page.update()
        except Exception as e:
            print(f"❌ Error en page.update(): {e}"); _tb.print_exc()

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

        # Obtener valores del date picker
        month, year = self.period_picker.value

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
            print(f"✅ {len(self.pollution_markers)} marcadores de contaminación agregados al mapa")
            if self._page:
                self._page.update()

    def _create_marker(self, lat, lon, color, icon, marker_data=None, tooltip_text=None, on_click=None):
        """Crea un marcador para el mini-mapa."""
        # Color de fondo con transparencia (solo si es un hex string)
        if isinstance(color, str) and color.startswith("#"):
            bg_color = color + "33"
        else:
            bg_color = "#33333333"  # fallback semitransparente

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
        month, year = self.period_picker.value

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

    def update_traffic_markers(self):
        """Actualiza los marcadores de tráfico en el mini-mapa."""
        print("\n🚗 update_traffic_markers llamado")
        
        if not hasattr(self, 'traffic_stations_info') or not self.traffic_stations_info:
            print("  ⚠️ No hay información de estaciones de tráfico para tiempo real")
            return

        self.traffic_markers = []

        for indicativo, info in self.traffic_stations_info.items():
            if not info['lat'] or not info['lon']:
                continue

            color = "#1E88E5" if indicativo == self.selected_traffic_station else "#90CAF9"

            marker_data = {
                "tipo": "trafico_historico",
                "indicativo": indicativo,
                "titulo": info['nombre']
            }

            tooltip = f"Estación: {info['nombre']}"
            if indicativo == self.selected_traffic_station:
                tooltip += " (Seleccionada)"

            # Crear marcador interactivo
            marker_content = ft.Container(
                width=30,
                height=30,
                bgcolor=color + "33",
                border_radius=15,
                alignment=ft.alignment.Alignment(0, 0),
                content=ft.Icon(
                    ft.icons.Icons.TRAFFIC,
                    color=color,
                    size=18
                ),
                tooltip=tooltip,
                on_click=lambda e, ind=indicativo: self.on_traffic_station_click(
                    ind)
            )

            marker = mapa.Marker(
                content=marker_content,
                coordinates=mapa.MapLatitudeLongitude(
                    info['lat'], info['lon']),
            )
            self.traffic_markers.append(marker)

        if self.marker_layer_ref.current:
            self.marker_layer_ref.current.markers = self.traffic_markers
            print(f"✅ {len(self.traffic_markers)} marcadores de tráfico agregados al mapa")
            if self._page:
                self._page.update()

    def update_historical_traffic_markers(self):
        """Actualiza los marcadores de tráfico usando datos históricos del parquet."""
        print("\n🚗 update_historical_traffic_markers llamado")
        
        if not hasattr(self, 'traffic_data_df') or self.traffic_data_df is None:
            print("  ⚠️ No hay datos de tráfico históricos cargados")
            return
        
        # Bug fix: leer mes/año desde el period_picker (los dropdowns ya no existen)
        month, year = self.period_picker.value
        
        if not month or not year:
            print("  ⚠️ No hay fecha seleccionada")
            return

        # Filtrar por fecha (YYYY-MM)
        # Convertir columna FECHA a string por si es Period o datetime
        month_int = int(month)
        date_str = f"{year}-{month_int:02}"
        
        try:
            fecha_col_str = self.traffic_data_df['FECHA'].astype(str)
        except Exception:
            fecha_col_str = self.traffic_data_df['FECHA']
        
        df_filtered = self.traffic_data_df[fecha_col_str.str.startswith(date_str)]
        print(f"  🔍 Registros encontrados para {date_str}: {len(df_filtered)}")

        if df_filtered.empty:
            print(f"  ⚠️ No hay datos de tráfico para {date_str}")
            # Mostrar mensaje informativo en el contenedor
            self.traffic_info_text.value = f"Sin datos disponibles para {date_str}"
            self.traffic_container.visible = True
            if self._page:
                self._page.update()
            return

        self.traffic_markers = []
        
        # Obtener estaciones en tiempo real para intentar matching de coordenadas
        try:
            from utils.RealTimeTrafficValencia import get_traffic_data
            rt_stations = get_traffic_data()
            desc_to_coords = {
                s.denominacion.upper(): (s.geo_point_2d['lat'], s.geo_point_2d['lon'])
                for s in rt_stations
                if s.geo_point_2d and 'lat' in s.geo_point_2d and 'lon' in s.geo_point_2d
            }
        except Exception as e:
            print(f"⚠️ Error al obtener estaciones realtime para matching: {e}")
            desc_to_coords = {}

        # Bug fix: usar hex string en lugar de ft.Colors.RED para permitir concatenación "33"
        COLOR_TRAFFIC = "#E53935"

        for _, row in df_filtered.iterrows():
            ata_id = row['ATA']
            desc = str(row['DESCRIPCION'])
            # Proteger contra IMD nulo o NaN
            try:
                imd = float(row['IMD'])
                if imd != imd:  # NaN check
                    imd = 0.0
            except (TypeError, ValueError):
                imd = 0.0
            
            # Intentar matching por descripción (exacto, insensible a mayúsculas)
            coords = desc_to_coords.get(desc.upper())
            
            if coords:
                lat, lon = coords
                
                marker_data = {
                    "tipo": "trafico_historico",
                    "titulo": desc,
                    "info": {
                        "ID ATA": str(ata_id),
                        "Ubicación": desc,
                        "IMD (Intensidad)": f"{imd:.1f} veh/día",
                        "Período": date_str
                    }
                }

                tooltip = f"ATA {ata_id}: {desc} (IMD: {imd:.0f})"

                marker = self._create_marker(
                    lat, lon, COLOR_TRAFFIC, ft.icons.Icons.TRAFFIC,
                    marker_data, tooltip,
                    on_click=lambda e, r=row.to_dict(): self.on_historical_traffic_click(r)
                )
                self.traffic_markers.append(marker)

        matched = len(self.traffic_markers)
        total = len(df_filtered)
        print(f"  📍 {matched}/{total} ubicaciones con coordenadas para {date_str}")

        if self.marker_layer_ref.current:
            self.marker_layer_ref.current.markers = self.traffic_markers
            print(f"✅ {matched} marcadores históricos de tráfico agregados")
            if self._page:
                self._page.update()

    def on_historical_traffic_click(self, row):
        """Manejador al hacer clic en un punto de tráfico histórico."""
        # row puede ser un dict (si venía de row.to_dict()) o una pandas Series
        desc = row['DESCRIPCION']
        ata = row['ATA']
        imd = row['IMD']
        fecha = row['FECHA']
        print(f"📍 Punto de tráfico seleccionado: {desc}")
        
        self.traffic_info_text.value = (
            f"🚗 ATA: {ata}\n"
            f"📍 {desc}\n"
            f"📈 IMD: {float(imd):.1f} veh/día\n"
            f"📅 Fecha: {fecha}"
        )
        self.traffic_container.visible = True
        
        if self._page:
            self._page.update()
    def update_weather_markers(self):
        """Actualiza los marcadores de estaciones meteorológicas."""
        print("\n🌧️ update_weather_markers llamado")

        self.weather_markers = []

        for indicativo, info in self.weather_stations_info.items():
            if not info['lat'] or not info['lon']:
                continue

            color = "#1565C0" if indicativo == self.selected_weather_station else "#90CAF9"

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

        info_text = f"📍 Estación: {sensor['nombre']}\n"
        info_text += f"💨 NO2: {no2:.1f} μg/m³\n" if no2 else "💨 NO2: N/A\n"
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
        

        month, year = self.period_picker.value
        print(f"\n🔍 Búsqueda solicitada: mes={month}, año={year}, capa={self.current_layer}")

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
            print("  → Actualizando marcadores de tráfico...")
            if hasattr(self, 'traffic_data_df'):
                self.update_historical_traffic_markers()
            else:
                self.update_traffic_markers()

    def on_year_change(self, e):
        """Manejador cuando cambia el año - actualiza los meses disponibles."""
        print(f"\n🔄 on_year_change llamado")
        self.update_date_ranges_for_layer(self.current_layer)
        self.on_date_change(e)

    def on_date_change(self, e):
        """Manejador de cambio de fecha."""
        month, year = self.period_picker.value
        print(f"\n📅 on_date_change llamado: mes={month}, año={year}, capa={self.current_layer}")

        # Auto-actualizar según la capa activa
        if self.current_layer == "pollution":
            print("  → Actualizando marcadores de contaminación...")
            self.update_pollution_markers()
        else:
            print(f"  ⚠️ Capa '{self.current_layer}' no soporta auto-actualización aún")

    def update_date_ranges_for_layer(self, layer: str):
        """Actualiza los rangos de fechas disponibles según la capa seleccionada."""
        if layer not in self.date_ranges:
            return

        range_config = self.date_ranges[layer]

        # Actualizar rangos en el picker (ajusta la selección si queda fuera)
        self.period_picker.set_range(
            year_start=range_config["year_start"],
            year_end=range_config["year_end"],
            month_start=range_config["month_start"],
            month_end=range_config["month_end"],
        )

        if self._page:
            self._page.update()
