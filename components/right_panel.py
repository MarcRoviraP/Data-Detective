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
import csv
import io
import base64
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg') # Backend no interactivo para hilos
import pandas as pd
import numpy as np
import threading
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak


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

        # Carpeta por defecto para exportaciones
        self.export_dir = os.path.join(os.getcwd(), "exports")
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

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

        # Contenedor para gráficos de Matplotlib
        self.chart_image = ft.Image(
            src="",
            visible=False,
            fit="contain",
            height=300,
            border_radius=10,
        )
        self.charts_container = ft.Container(
            content=ft.Column([
                ft.Text("📊 ANÁLISIS VISUAL DE DATOS", size=14,
                        weight=ft.FontWeight.BOLD),
                self.chart_image
            ]),
            padding=10,
            bgcolor="#161b22",
            border_radius=10,
            visible=False,
            margin=ft.margin.only(bottom=20)
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
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                icon="sensors",
                                on_click=lambda _: self.update_map_layer(
                                    "pollution"),
                                bgcolor=ft.Colors.GREEN if self.current_layer == "pollution" else ft.Colors.AMBER,
                                color=ft.Colors.WHITE if self.current_layer == "pollution" else ft.Colors.BLACK,
                                expand=True
                            ),
                            ft.ElevatedButton(
                                "Precipitaciones",
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                icon="grain",
                                on_click=lambda _: self.update_map_layer(
                                    "rain"),
                                bgcolor=ft.Colors.BLUE if self.current_layer == "rain" else ft.Colors.AMBER,
                                color=ft.Colors.WHITE if self.current_layer == "rain" else ft.Colors.BLACK,
                                expand=True
                            ),
                            ft.ElevatedButton(
                                "Tráfico",
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
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
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
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

                    # Botones de Exportación
                    ft.Row(
                        controls=[
                            ft.Text("Exportar:", size=12,
                                    weight=ft.FontWeight.BOLD),
                            ft.TextButton(
                                "JSON",
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                icon=ft.Icons.DOWNLOAD,
                                on_click=self._on_export_json_click,
                            ),
                            ft.TextButton(
                                "CSV",
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                icon=ft.Icons.FILE_DOWNLOAD,
                                on_click=self._on_export_csv_click,
                            ),
                            ft.ElevatedButton(
                                "Generar Informe PDF",
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                icon=ft.Icons.PICTURE_AS_PDF,
                                bgcolor=ft.Colors.RED_800,
                                color=ft.Colors.WHITE,
                                on_click=self._on_export_pdf_click,
                            ),
                        ],
                        spacing=10,
                    ),

                    # Resúmenes de datos seleccionados (Clima, Calidad Aire, Tráfico)
                    self.weather_container,
                    self.pollution_container,
                    self.traffic_container,

                    # Mini mapa para mostrar la ubicación del sensor seleccionado
                    ft.Text("Ubicación de Sensores", size=14,
                            weight=ft.FontWeight.BOLD),

                    # Mapa
                    ft.Container(
                        content=self._create_mini_map(),
                        height=350,
                    ),
                    
                    # Gráficos (DEBAJO DEL MAPA)
                    self.charts_container,
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
            if hasattr(self, 'traffic_data_df') and self.traffic_data_df is not None:
                self.update_historical_traffic_markers()

        # Actualizar gráficos al cambiar de capa (en hilo separado)
        import threading
        thread = threading.Thread(target=self._update_charts, daemon=True)
        thread.start()

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

        if aemet_data is not None:
            self.aemet_data = aemet_data.get('aemet_data', {})
            self.weather_stations_info = aemet_data.get(
                'weather_stations_info', {})

        if traffic_data is not None:
            # Si es un DataFrame (parquet)
            import pandas as pd
            if isinstance(traffic_data, pd.DataFrame):
                object.__setattr__(self, 'traffic_data_df', traffic_data)
                traffic_coords_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                                   "data", "trafico_valencia_coords.parquet")
                if os.path.exists(traffic_coords_path):
                    object.__setattr__(self, 'traffic_coords_df', pd.read_parquet(
                        traffic_coords_path, engine='pyarrow'))
                else:
                    object.__setattr__(self, 'traffic_coords_df', None)
            else:
                object.__setattr__(self, 'traffic_data',
                                   traffic_data.get('traffic_data', {}))
                object.__setattr__(self, 'traffic_stations_info', traffic_data.get(
                    'traffic_stations_info', {}))

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
                # Construir info solo con datos válidos
                info_p = {
                    "Estación": sensor['nombre'],
                    "Código": sensor['cod'],
                    "Período": f"{month}/{year}"
                }

                # Añadir métricas solo si existen y son válidas
                for label, key in [("NO2 Promedio", 'no2_avg'), ("O3 Promedio", 'o3_avg'), ("PM10 Promedio", 'pm10_avg')]:
                    val = sensor.get(key)
                    if val is not None and str(val).lower() not in ["none", "nan", "n/a", "-"]:
                        try:
                            info_p[label] = f"{float(val):.1f} μg/m³"
                        except:
                            pass

                marker_data = {
                    "tipo": "contaminacion_historica",
                    "titulo": sensor['nombre'],
                    "icon": ft.icons.Icons.CLOUD,
                    "color": color,
                    "info": info_p
                }

                # Crear tooltip simplificado y amigable
                no2_text = f"{sensor['no2_avg']:.1f} μg/m³" if sensor['no2_avg'] else "N/A"
                tooltip_text = f"🍀 Estación: {sensor['nombre']}\n💨 Aire (NO2): {no2_text}"

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
            print(
                f"✅ {len(self.pollution_markers)} marcadores de contaminación agregados al mapa")
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
            tm_mes = weather.get('tm_mes')
            p_mes = weather.get('p_mes')
            tm_max = weather.get('tm_max')
            tm_min = weather.get('tm_min')

            self.weather_container.content.controls[0].value = "🌦️ RESUMEN DEL CLIMA"

            lines = [f"📍 Estación: {station_name}\n"]

            # Temperatura media y clasificación
            if tm_mes and str(tm_mes) not in ["N/A", "None", "nan"]:
                try:
                    temp = float(tm_mes)
                    if temp < 10:
                        clado_temp = "❄️ Frío"
                    elif temp < 20:
                        clado_temp = "⛅ Templado"
                    elif temp < 30:
                        clado_temp = "☀️ Cálido"
                    else:
                        clado_temp = "🔥 Muy caluroso"
                    lines.append(
                        f"🌡️ Temperatura media: {tm_mes}°C ({clado_temp})")
                except:
                    lines.append(f"🌡️ Temperatura media: {tm_mes}°C")

            # Máximas y mínimas
            t_max_valid = tm_max and str(tm_max) not in ["N/A", "None", "nan"]
            t_min_valid = tm_min and str(tm_min) not in ["N/A", "None", "nan"]
            if t_max_valid or t_min_valid:
                max_str = f"{tm_max}°C" if t_max_valid else "?"
                min_str = f"{tm_min}°C" if t_min_valid else "?"
                lines.append(f"📈 Máxima: {max_str} | 📉 Mínima: {min_str}")

            # Lluvia
            if p_mes and str(p_mes) not in ["N/A", "None", "nan"]:
                lines.append(f"🌧️ Lluvia total: {p_mes} mm acumulados")

            self.weather_info_text.value = "\n".join(lines)
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

            tooltip = f"📍 {info['nombre']}\n🚗 Pulsa para ver datos de tráfico"
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
            print(
                f"✅ {len(self.traffic_markers)} marcadores de tráfico agregados al mapa")
            if self._page:
                self._page.update()

    def update_historical_traffic_markers(self):
        """Actualiza los marcadores de tráfico usando datos históricos del parquet."""
        print("\n🚗 update_historical_traffic_markers llamado")
        import pandas as pd

        if not hasattr(self, 'traffic_data_df') or self.traffic_data_df is None:
            print("  ⚠️ No hay datos de tráfico históricos cargados")
            return
        if not hasattr(self, 'traffic_coords_df') or self.traffic_coords_df is None:
            print("  ⚠️ No hay datos de coordenadas de tráfico cargados")
            return

        month, year = self.period_picker.value

        if not month or not year:
            print("  ⚠️ No hay fecha seleccionada")
            return

        # Filtrar por fecha (YYYY-MM)
        # Convertir columna FECHA a string por si es Period o datetime
        month_int = int(month)
        date_str = f"{year}-{month_int:02}"

        df = self.traffic_data_df.copy()
        df['FECHA'] = pd.to_datetime(df['FECHA'])
        df_filtered = df[df['FECHA'] == date_str]
        print(
            f"  🔍 Registros encontrados para {date_str}: {df_filtered.shape}")

        if df_filtered.empty:
            print(f"  ⚠️ No hay datos de tráfico para {date_str}")
            # Mostrar mensaje informativo en el contenedor
            self.traffic_info_text.value = f"Sin datos disponibles para {date_str}"
            self.traffic_container.visible = True
            if self._page:
                self._page.update()
            return

        self.traffic_markers = []

        # Guardar en un dict para acceso rapido (ATA -> {lat, lon, desc})
        coords_dict = {}
        for _, row_c in self.traffic_coords_df.iterrows():
            coords_dict[row_c['ATA']] = {
                'lat': row_c['LAT'],
                'lon': row_c['LON'],
                'desc': row_c['DESCRIPCION']
            }

        # Bug fix: usar hex string en lugar de ft.Colors.RED para permitir concatenación "33"
        COLOR_TRAFFIC = "#E53935"

        for _, row in df_filtered.iterrows():
            ata_id = row['ATA']
            imd = row['IMD']

            coord = coords_dict.get(ata_id)
            if not coord or pd.isna(coord['lat']) or pd.isna(coord['lon']):
                continue

            lat = coord['lat']
            lon = coord['lon']
            desc = coord.get('desc', f"ATA {ata_id}")

            # Asignar color dinámico según intensidad (IMD)
            imd_val = int(imd)
            if imd_val < 5000:
                color = ft.Colors.GREEN_400
            elif imd_val < 15000:
                color = ft.Colors.LIME_500
            elif imd_val < 30000:
                color = ft.Colors.AMBER_500
            elif imd_val < 50000:
                color = ft.Colors.ORANGE_500
            elif imd_val < 80000:
                color = ft.Colors.RED_500
            else:
                color = ft.Colors.RED_900

            marker_data = {
                "tipo": "trafico_historico",
                "titulo": desc,
                "info": {
                    "ID ATA": ata_id,
                    "Ubicación": desc,
                    "IMD (Intensidad)": f"{int(imd)} veh/día",
                    "Período": date_str
                }
            }

            tooltip = f"📍 {desc}\n🚗 {int(imd):,} vehículos diarios (Promedio)"

            marker = self._create_marker(
                lat, lon, color, ft.icons.Icons.TRAFFIC,
                marker_data, tooltip,
                on_click=lambda e: self.on_historical_traffic_click(row, desc)
            )
            self.traffic_markers.append(marker)

        matched = len(self.traffic_markers)
        total = len(df_filtered)
        print(f"  📍 {matched}/{total} ubicaciones con coordenadas para {date_str}")

        if self.marker_layer_ref.current:
            self.marker_layer_ref.current.markers = self.traffic_markers
            print(
                f"✅ {len(self.traffic_markers)} marcadores históricos de tráfico agregados")
            if self._page:
                self._page.update()

    def on_historical_traffic_click(self, row, desc=None):
        """Manejador al hacer clic en un punto de tráfico histórico con info amigable."""
        final_desc = desc if desc else "Ubicación desconocida"
        print(f"📍 Punto de tráfico seleccionado: {final_desc}")

        # Actualizar título del contenedor para que sea dinámico
        self.pollution_container.content.controls[0].value = "📊 ESTADÍSTICAS DE TRÁFICO"

        imd = int(row['IMD'])
        # Clasificación amigable del nivel de tráfico
        if imd < 10000:
            estado = "🟢 Fluido (Poco tráfico)"
        elif imd < 25000:
            estado = "🟡 Moderado"
        elif imd < 45000:
            estado = "🟠 Denso (Mucho tráfico)"
        else:
            estado = "🔴 Saturado (Tráfico intenso)"

        # Formatear fecha
        fecha = row['FECHA']
        fecha_str = f"{MONTH_NAMES[fecha.month-1]} {fecha.year}" if hasattr(
            fecha, 'month') else str(fecha)

        self.pollution_info_text.value = (
            f"📍 Punto de medida:\n   {final_desc}\n\n"
            f"🚗 Tráfico promedio:\n   {imd:,} vehículos cada día\n\n"
            f"📈 Nivel de congestión:\n   {estado}\n\n"
            f"📅 Mes consultado: {fecha_str}\n"
            f"🆔 Identificador: {row['ATA']}"
        )
        self.pollution_container.visible = True

        if self._page:
            self._page.update()

    # ── EXPORT LOGIC ──────────────────────────────────────────────────────

    async def _on_export_json_click(self, e):
        await self.start_export("json")

    async def _on_export_csv_click(self, e):
        await self.start_export("csv")

    async def _on_export_pdf_click(self, e):
        await self.start_export("pdf")

    def _get_save_path_tk(self, default_filename, filetypes):
        """Muestra el diálogo de Tkinter en un hilo seguro."""
        import tkinter as tk
        from tkinter import filedialog

        path = None
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.asksaveasfilename(
                initialdir=self.export_dir,
                initialfile=default_filename,
                filetypes=filetypes,
                title="Guardar exportación"
            )
            root.destroy()
        except:
            pass
        return path

    async def start_export(self, format_type):
        """Usa un hilo separado para el diálogo y guarda el archivo."""
        if not self.data_loaded:
            self._show_snackbar(
                "⚠️ Espera a que los datos se carguen completamente.")
            return

        try:
            data = self._get_current_data_list()
            if not data:
                self._show_snackbar(
                    "⚠️ No hay datos en la visualización actual para exportar.")
                return

            month, year = self.period_picker.value
            default_filename = f"VLC_{self.current_layer}_{year}_{month}.{format_type}"

            # Tipos de archivo para el diálogo
            if format_type == "json":
                filetypes = [("JSON files", "*.json")]
            elif format_type == "csv":
                filetypes = [("CSV files", "*.csv")]
            else:
                filetypes = [("PDF files", "*.pdf")]

            # Ejecutar diálogo en un hilo para no bloquear el bridge de Flet
            import asyncio
            loop = asyncio.get_event_loop()
            path = await loop.run_in_executor(None, self._get_save_path_tk, default_filename, filetypes)

            if path:
                if format_type == "json":
                    self._save_json(path, data)
                elif format_type == "csv":
                    self._save_csv(path, data)
                elif format_type == "pdf":
                    self._save_pdf(path, data)

                self._show_snackbar(
                    f"✅ Archivo guardado: {os.path.basename(path)}")
                print(f"📦 Exportación completada: {path}")

        except Exception as ex:
            print(f"❌ Error en exportación: {ex}")
            self._show_snackbar(f"❌ Error: {str(ex)}")

    def _get_current_data_list(self):
        """Obtiene la lista de datos según la capa y fecha actual."""
        month, year = self.period_picker.value

        if self.current_layer == "pollution":
            return self.filter_sensors_by_date(month, year)

        elif self.current_layer == "rain":
            results = []
            month_int = int(month)
            date_key = f"{year}-{month_int:02}"

            for ind, info in self.weather_stations_info.items():
                station_data = self.aemet_data.get(ind, {})
                weather = station_data.get(
                    date_key) or station_data.get(f"{year}-{month_int}")
                if weather:
                    entry = {"Estación": info['nombre'],
                             "Indicativo": ind, "Fecha": date_key}
                    entry.update(weather)
                    results.append(entry)
            return results

        elif self.current_layer == "traffic":
            if not hasattr(self, 'traffic_data_df') or self.traffic_data_df is None:
                return []

            month_int = int(month)
            date_str = f"{year}-{month_int:02}"

            df = self.traffic_data_df
            df_filtered = df[df['FECHA'] == date_str].copy()

            # Limpiar nombres de columnas (quitar saltos de línea \r\n)
            df_filtered.columns = [c.strip() for c in df_filtered.columns]

            # Formatear fecha para el PDF/JSON: dd-MM-YYYY (usamos dia 01)
            df_filtered['Fecha_Formato'] = f"01-{month_int:02}-{year}"

            # Enriquecer con descripciones si están disponibles
            if hasattr(self, 'traffic_coords_df') and self.traffic_coords_df is not None:
                coords_map = self.traffic_coords_df.set_index(
                    'ATA')['DESCRIPCION'].to_dict()
                # Si no hay descripción, usar el ID de ATA para que no salga 'nan'
                df_filtered['Descripcion'] = df_filtered['ATA'].map(coords_map).fillna(
                    "Punto tráfico " + df_filtered['ATA'].astype(str))
            else:
                df_filtered['Descripcion'] = "Punto tráfico " + \
                    df_filtered['ATA'].astype(str)

            # Arreglar error de JSON: Convertir Timestamps de pandas a strings
            for col in df_filtered.columns:
                if pd.api.types.is_datetime64_any_dtype(df_filtered[col]):
                    df_filtered[col] = df_filtered[col].dt.strftime('%Y-%m-%d')

            # REQUISITO: No guardar FECHA_RAW
            if 'FECHA_RAW' in df_filtered.columns:
                df_filtered = df_filtered.drop(columns=['FECHA_RAW'])

            return df_filtered.to_dict('records')

        return []

    def _save_json(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _save_csv(self, path, data):
        if not data:
            return
        keys = data[0].keys()
        with open(path, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

    def _save_pdf(self, path, data):
        """Genera un informe PDF profesional con métricas detalladas y gráficas."""
        import matplotlib.pyplot as plt
        import numpy as np

        month, year = self.period_picker.value
        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Estilos personalizados
        title_style = styles['Title']
        title_style.textColor = colors.HexColor("#1A237E")  # Azul oscuro
        subtitle_style = styles['Heading2']
        subtitle_style.textColor = colors.HexColor("#0D47A1")
        normal_style = styles['Normal']

        # 1. ENCABEZADO
        elements.append(
            Paragraph(f"VLC URBAN INTEL - INFORME HISTÓRICO", title_style))
        elements.append(Paragraph(
            f"Análisis detallado de {self.current_layer.upper()}", subtitle_style))
        elements.append(
            Paragraph(f"<b>Período:</b> {MONTH_NAMES[int(month)-1]} {year}", normal_style))
        elements.append(Paragraph(
            f"<b>Fecha de generación:</b> {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
        elements.append(Spacer(1, 20))

        # 2. RESUMEN EJECUTIVO
        avg_val = 0
        max_val = 0
        if self.current_layer == "pollution" and data:
            vals = [d.get('no2_avg', 0)
                    for d in data if d.get('no2_avg') is not None]
            if vals:
                avg_val = np.mean(vals)
                max_val = np.max(vals)
                elements.append(Paragraph(
                    f"<b>INFO - Calidad del Aire:</b> En este período, el promedio de NO2 en la ciudad fue de {avg_val:.2f} μg/m³, con un pico máximo detectado de {max_val:.2f} μg/m³.", normal_style))
        elif self.current_layer == "rain" and data:
            vals = [float(d.get('p_mes', 0))
                    for d in data if str(d.get('p_mes')) != 'N/A']
            if vals:
                total_rain = np.sum(vals)
                elements.append(Paragraph(
                    f"<b>INFO - Resumen Meteorológico:</b> Se registró una precipitación total acumulada de {total_rain:.1f} mm entre todas las estaciones consultadas.", normal_style))
        elif self.current_layer == "traffic" and data:
            imds = [d.get('IMD', 0) for d in data]
            if imds:
                avg_traffic = np.mean(imds)
                max_traffic = np.max(imds)
                total_est = len(data)
                elements.append(Paragraph(
                    f"<b>INFO - Análisis de Tráfico:</b> Se han analizado {total_est} puntos de medición. La intensidad media detectada es de {int(avg_traffic)} vehículos/día, con un flujo máximo de {int(max_traffic)} vehículos/día en el punto más congestionado.", normal_style))

        elements.append(Spacer(1, 15))

        # 3. GRÁFICA DE DATOS
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(7, 4))

        if self.current_layer == "pollution":
            # Gráfica de barras comparativa (Top 8 estaciones)
            stations = [d.get('nombre', 'Est.')[:12] for d in data[:8]]
            no2_vals = [d.get('no2_avg', 0) or 0 for d in data[:8]]
            o3_vals = [d.get('o3_avg', 0) or 0 for d in data[:8]]

            x = np.arange(len(stations))
            width = 0.35
            ax.bar(x - width/2, no2_vals, width, label='NO2', color='#E53935')
            ax.bar(x + width/2, o3_vals, width, label='O3', color='#FFB300')
            ax.set_ylabel('Concentración (μg/m³)')
            ax.set_title('Comparativa de Contaminantes por Estación')
            ax.set_xticks(x)
            ax.set_xticklabels(stations, rotation=45, ha='right')
            ax.legend()

        elif self.current_layer == "rain":
            # Gráfica de precipitaciones
            names = [d.get('Estación', 'Est.')[:12] for d in data[:10]]
            rain = [float(d.get('p_mes', 0)) if str(d.get('p_mes'))
                    != 'N/A' else 0 for d in data[:10]]
            ax.bar(names, rain, color='#1E88E5')
            ax.set_ylabel('Precipitación (mm)')
            ax.set_title('Precipitación Mensual por Estación')
            plt.xticks(rotation=45, ha='right')
        elif self.current_layer == "traffic":
            # Búsqueda de los Top 10 puntos de mayor intensidad
            data_sorted = sorted(data, key=lambda x: x.get(
                'IMD', 0), reverse=True)[:10]
            names = [str(d.get('Descripcion') or d.get('ATA'))[:15]
                     for d in data_sorted]
            imds = [d.get('IMD', 0) for d in data_sorted]

            ax.barh(names, imds, color='#4527A0')
            ax.set_xlabel('Vehículos / Día')
            ax.set_title('Top 10 Puntos de Mayor Tráfico')
            ax.invert_yaxis()  # Los más ocupados arriba

        plt.tight_layout()
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', dpi=150)
        img_buf.seek(0)
        plt.close()

        elements.append(Image(img_buf, width=450, height=250))
        elements.append(Spacer(1, 25))

        # 4. DESGLOSE DE DATOS
        if self.current_layer == "traffic":
            # REQUISITO: Top 100 Max IMD
            elements.append(PageBreak())
            elements.append(
                Paragraph("[+] Puntos de MAXIMA Intensidad (Top 100)", subtitle_style))
            elements.append(Spacer(1, 10))

            data_top = sorted(data, key=lambda x: x.get(
                'IMD', 0), reverse=True)[:100]
            header = ['ATA', 'Calle / Descripción', 'IMD (Veh/día)', 'Fecha']
            cols = ['ATA', 'Descripcion', 'IMD', 'Fecha_Formato']
            self._create_pdf_table(elements, header, cols, data_top)

            # REQUISITO: Top 100 Min IMD
            elements.append(PageBreak())
            elements.append(
                Paragraph("[-] Puntos de MINIMA Intensidad (Top 100)", subtitle_style))
            elements.append(Spacer(1, 10))

            data_bottom = sorted(data, key=lambda x: x.get('IMD', 0))[:100]
            self._create_pdf_table(elements, header, cols, data_bottom)
        else:
            # Desglose estándar para otras capas (Top 25)
            elements.append(
                Paragraph("LISTADO DE DATOS (Desglose de registros):", subtitle_style))
            elements.append(Spacer(1, 10))

            if data:
                if self.current_layer == "pollution":
                    header = ['Estación',
                              'NO2 (μg/m³)', 'O3 (μg/m³)', 'PM10 (μg/m³)']
                    cols = ['nombre', 'no2_avg', 'o3_avg', 'pm10_avg']
                elif self.current_layer == "rain":
                    header = [
                        'Estación', 'Prec. (mm)', 'T.Media (°C)', 'T.Max (°C)', 'T.Min (°C)']
                    cols = ['Estación', 'p_mes', 'tm_mes', 'ta_max', 'ta_min']
                else:
                    header = list(data[0].keys())[:5]
                    cols = header

                self._create_pdf_table(elements, header, cols, data[:25])

        # Footer
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "<font color='grey' size='8'>Data Detective VLC Intel - Proyecto de Análisis Urbanístico</font>", styles['Normal']))

        doc.build(elements)

    def _create_pdf_table(self, elements, header, cols, data_slice):
        """Helper para crear tablas estilizadas en el PDF."""
        table_data = [header]
        for row in data_slice:
            formatted_row = []
            for c in cols:
                val = row.get(c, "-")
                # Limpiar valores nulos (NaN o None)
                if val is None or (isinstance(val, float) and np.isnan(val)) or str(val).lower() == "nan":
                    formatted_row.append("-")
                elif isinstance(val, (float, int)):
                    formatted_row.append(f"{val:.1f}")
                else:
                    # Detectar formato AEMET: 25.6(05) -> 25.6 (Día 05)
                    text_val = str(val)
                    if "(" in text_val and ")" in text_val and self.current_layer == "rain":
                        try:
                            main_val = text_val.split("(")[0]
                            day_val = text_val.split("(")[1].split(")")[0]
                            formatted_row.append(f"{main_val} (Día {day_val})")
                        except:
                            formatted_row.append(text_val[:30])
                    else:
                        formatted_row.append(text_val[:30])
            table_data.append(formatted_row)

        # Ajustar anchos de columna según la capa
        if self.current_layer == "traffic":
            col_widths = [60, 240, 90, 90]
        elif self.current_layer == "pollution":
            col_widths = [180, 100, 100, 100]
        else:  # rain o genérico
            col_widths = [160, 80, 80, 80, 80][:len(header)]

        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#303F9F")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F5F5F5")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.whitesmoke, colors.HexColor("#E3F2FD")])
        ]))
        elements.append(t)

    def _show_snackbar(self, message):
        if self._page:
            self._page.snack_bar = ft.SnackBar(ft.Text(message))
            self._page.snack_bar.open = True
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

            tooltip = f"🌦️ Estación: {info['nombre']}\n📍 Toca para ver datos del clima"
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

        # Asegurar que el título sea correcto para contaminación
        self.pollution_container.content.controls[0].value = "🍀 CALIDAD DEL AIRE"

        # Clasificación amigable de NO2
        if no2:
            if no2 < 20:
                estado_no2 = "🟢 Excelente"
            elif no2 < 40:
                estado_no2 = "🟡 Bueno"
            elif no2 < 100:
                estado_no2 = "🟠 Regular"
            else:
                estado_no2 = "🔴 Malo (Mucha contaminación)"
        else:
            estado_no2 = "Desconocido"

        info_text = (
            f"📍 Estación de control:\n   {sensor['nombre']}\n\n"
            f"💨 Calidad del aire:\n   {estado_no2}\n\n"
        )

        has_metrics = False
        metrics_block = "📊 Mediciones promedio:\n"

        if no2 and str(no2) not in ["None", "nan", "N/A"]:
            metrics_block += f"   • Dióxido de Nitrógeno: {no2:.1f} μg/m³\n"
            has_metrics = True
        if o3 and str(o3) not in ["None", "nan", "N/A"]:
            metrics_block += f"   • Ozono (O3): {o3:.1f} μg/m³\n"
            has_metrics = True
        if pm10 and str(pm10) not in ["None", "nan", "N/A"]:
            metrics_block += f"   • Partículas (PM10): {pm10:.1f} μg/m³\n"
            has_metrics = True

        if has_metrics:
            info_text += metrics_block

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
        if not self.data_loaded:
            missing = []
            if not hasattr(self, 'traffic_data_df') and not hasattr(self, 'traffic_data'):
                missing.append('Traffic Data')
            if not hasattr(self, 'aemet_data'):
                missing.append('AEMET Data')
            if not hasattr(self, 'metadata'):
                missing.append('Pollution Data')
            print(
                f"  ⚠️ Datos aún cargando, por favor espere... Falta: {', '.join(missing)}")
            if self._page:
                self._page.snack_bar = ft.SnackBar(
                    ft.Text(f"Los datos aún se están cargando... (Falta: {', '.join(missing)})"))
                self._page.snack_bar.open = True
                self._page.update()
            return

        month, year = self.period_picker.value
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
            print("  → Actualizando marcadores de tráfico...")
            if hasattr(self, 'traffic_data_df'):
                self.update_historical_traffic_markers()
            else:
                self.update_traffic_markers()

        # Actualizar gráficos en un hilo separado para no bloquear la UI
        import threading
        thread = threading.Thread(target=self._update_charts, daemon=True)
        thread.start()

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
            print(f"  → Actualizando marcadores de '{self.current_layer}'...")
            self.on_search_click(None)

        # Actualizar gráficos cada vez que cambia la fecha (en hilo separado)
        import threading
        thread = threading.Thread(target=self._update_charts, daemon=True)
        thread.start()

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

    def _get_current_data_list(self):
        """Obtiene la lista de datos filtrados para la capa actual."""
        try:
            month, year = self.period_picker.value
            if not month or not year:
                return []
                
            month_int = int(month)
            year_int = int(year)
            
            print(f"📊 Buscando datos para gráficos: {month_int}/{year_int} (Capa: {self.current_layer})")
            
            if self.current_layer == "pollution":
                data = self.filter_sensors_by_date(month, year)
                print(f"📊 Polución: {len(data) if data else 0} registros encontrados")
                return data if isinstance(data, list) else []
            
            elif self.current_layer == "rain":
                if hasattr(self, 'aemet_data') and isinstance(self.aemet_data, dict) and 'aemet_data' in self.aemet_data:
                    filtered_data = []
                    target_date = f"{year_int}-{month_int:02d}"
                    station_data_dict = self.aemet_data['aemet_data']
                    
                    for indicativo, station_dates in station_data_dict.items():
                        if isinstance(station_dates, dict) and target_date in station_dates:
                            item = station_dates[target_date].copy()
                            if indicativo in self.weather_stations_info:
                                item['Estación'] = self.weather_stations_info[indicativo]['nombre']
                            filtered_data.append(item)
                    
                    print(f"📊 Clima: {len(filtered_data)} registros encontrados para {target_date}")
                    return filtered_data
            
            elif self.current_layer == "traffic":
                if hasattr(self, 'traffic_data_df') and self.traffic_data_df is not None:
                    df = self.traffic_data_df
                    target_date = f"{year_int}-{month_int:02d}"
                    if 'FECHA' in df.columns:
                        mask = df['FECHA'] == target_date
                        df_filtered = df[mask].copy()
                        
                        if hasattr(self, 'traffic_coords_df') and self.traffic_coords_df is not None:
                            coords_map = self.traffic_coords_df.set_index('ATA')['DESCRIPCION'].to_dict()
                            df_filtered['Descripcion'] = df_filtered['ATA'].map(coords_map).fillna(df_filtered['ATA'])
                        
                        data_list = df_filtered.to_dict('records')
                        print(f"📊 Tráfico: {len(data_list)} registros encontrados para {target_date}")
                        return data_list
        except Exception as e:
            print(f"❌ Error en _get_current_data_list: {e}")
                
        return []

    def _update_charts(self):
        """Genera y muestra gráficos de Matplotlib basados en los datos actuales."""
        if not self.data_ready_for_charts():
            self.charts_container.visible = False
            if self._page:
                self._page.update()
            return

        try:
            data = self._get_current_data_list()
            if not data:
                self.charts_container.visible = False
                return

            # Configuración de estilo Matplotlib (Dark Mode compatible)
            plt.style.use('dark_background')
            plt.rcParams['figure.facecolor'] = '#161b22'
            plt.rcParams['axes.facecolor'] = '#161b22'
            
            fig, ax = plt.subplots(figsize=(7, 4))

            if self.current_layer == "pollution":
                # Gráfica de barras comparativa (Top 8 estaciones)
                data_subset = [d for d in data if isinstance(d, dict) and 'nombre' in d][:8]
                if not data_subset: 
                    self.charts_container.visible = False
                    return
                
                stations = [str(d.get('nombre', 'Est.'))[:12] for d in data_subset]
                no2_vals = [float(d.get('no2_avg', 0) or 0) for d in data_subset]
                o3_vals = [float(d.get('o3_avg', 0) or 0) for d in data_subset]

                x = np.arange(len(stations))
                width = 0.35
                ax.bar(x - width/2, no2_vals, width, label='NO2', color='#E53935')
                ax.bar(x + width/2, o3_vals, width, label='O3', color='#FFB300')
                ax.set_ylabel('Concentración (ug/m3)')
                ax.set_title('Calidad del Aire por Estación', color='white')
                ax.set_xticks(x)
                ax.set_xticklabels(stations, rotation=45, ha='right', color='white')
                ax.legend()

            elif self.current_layer == "rain":
                # Gráfica de precipitaciones
                data_subset = [d for d in data if isinstance(d, dict) and 'Estación' in d][:10]
                if not data_subset:
                    self.charts_container.visible = False
                    return
                    
                names = [str(d.get('Estación', 'Est.'))[:12] for d in data_subset]
                rain = [float(d.get('p_mes', 0)) if str(d.get('p_mes')) != 'N/A' and d.get('p_mes') is not None else 0 for d in data_subset]
                ax.bar(names, rain, color='#1E88E5')
                ax.set_ylabel('Precipitación (mm)')
                ax.set_title('Precipitación Mensual por Estación', color='white')
                plt.xticks(rotation=45, ha='right', color='white')

            elif self.current_layer == "traffic":
                # Asegurar que IMD sea numérico y filtrar dicts
                clean_data = []
                for d in data:
                    if isinstance(d, dict):
                        d_copy = d.copy()
                        val = d_copy.get('IMD')
                        try:
                            d_copy['IMD_num'] = float(val) if val is not None else 0
                        except:
                            d_copy['IMD_num'] = 0
                        clean_data.append(d_copy)
                
                if not clean_data:
                    self.charts_container.visible = False
                    return
                    
                data_sorted = sorted(clean_data, key=lambda x: x.get('IMD_num', 0), reverse=True)[:10]
                names = [str(d.get('Descripcion') or d.get('ATA'))[:20] for d in data_sorted]
                imds = [d.get('IMD_num', 0) for d in data_sorted]

                ax.barh(names, imds, color='#7C4DFF')
                ax.set_xlabel('Vehículos / Día')
                ax.set_title('Puntos de Mayor Tráfico', color='white')
                ax.invert_yaxis()
                plt.xticks(color='white')
                plt.yticks(color='white')

            plt.tight_layout()
            
            # Guardar en buffer
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png', dpi=120, transparent=True)
            img_buf.seek(0)
            
            # Convertir a Base64 para Flet
            img_b64 = base64.b64encode(img_buf.read()).decode('utf-8')
            plt.close(fig)
            
            # Actualizar componente Flet usando el esquema data URI para compatibilidad
            self.chart_image.src = f"data:image/png;base64,{img_b64}"
            self.chart_image.visible = True
            self.charts_container.visible = True
            
        except Exception as e:
            print(f"❌ Error al generar gráfico en UI: {e}")
            import traceback
            traceback.print_exc()
            self.charts_container.visible = False
        
        if self._page:
            self._page.update()

    def data_ready_for_charts(self):
        """Verifica si hay datos suficientes para mostrar gráficos."""
        if not self.data_loaded:
            return False
            
        month, year = self.period_picker.value
        if not month or not year:
            return False
            
        return True
