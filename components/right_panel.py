"""
Panel lateral derecho con archivo histórico y análisis.
Reescrito para mayor robustez y manejo de estado.
"""

import flet as ft
from config.theme import COLORS
from .ui_elements import UIElements
import os

class RightPanel(ft.Container):
    """
    Panel lateral derecho con archivo histórico y datos consolidados.
    Maneja la visualización de estadísticas históricas y navegación por fechas.
    """
    
    def __init__(self, page: ft.Page = None):
        # 1. Inicialización de estado
        self._page_ref = page
        self.current_year = 2024
        self.current_month = 12
        self.historical_stats = {}
        self.completeness = 0
        
        # 2. Referencias a componentes UI (para actualizaciones parciales)
        self.stats_column = ft.Column(spacing=10) # Contenedor de tarjetas
        self.completeness_text = ft.Text(
            value="---%", 
            size=40, 
            weight=ft.FontWeight.BOLD
        )
        
        # 3. Configuración del Contenedor Principal
        super().__init__(
            width=400,
            bgcolor=COLORS["bg_white"],
            padding=30,
            content=self._build_layout()
        )
        
        # 4. Carga inicial de datos
        self.load_historical_data()

    def _build_layout(self):
        """Construye la estructura principal del panel."""
        return ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self._build_header_section(),
                self._build_timeline_decoration(),
                self._build_title_section(),
                self._build_controls_section(),
                self._build_stats_section(),
                self._build_snapshot_section(),
                self._build_events_section(),
                self._build_reliability_section(),
            ]
        )

    # --- Secciones del UI ---

    def _build_header_section(self):
        """Crea el header con selectores de fecha."""
        # Configuración de opciones
        year_options = [ft.dropdown.Option(str(y)) for y in range(2025, 1993, -1)]
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        month_options = [ft.dropdown.Option(key=str(i+1), text=m) for i, m in enumerate(months)]

        # Creación de Dropdowns
        self.year_dropdown = ft.Dropdown(
            width=100,
            value=str(self.current_year),
            options=year_options,
            text_size=13,
            height=40,
            content_padding=10,
            border_color=COLORS["border_light"],
            dense=True,
            bgcolor=COLORS["bg_light"],
            border_radius=8,
            label="Año",
            label_style=ft.TextStyle(size=10, color=COLORS["text_gray"])
        )
        # Asignación de evento explícita (Fix para Flet)
        self.year_dropdown.on_change = self._on_year_changed
        self.year_dropdown.text_style = ft.TextStyle(color=COLORS["text_black"], weight=ft.FontWeight.BOLD)

        self.month_dropdown = ft.Dropdown(
            width=100,
            value=str(self.current_month),
            options=month_options,
            text_size=13,
            height=40,
            content_padding=10,
            border_color=COLORS["border_light"],
            dense=True,
            bgcolor=COLORS["bg_light"],
            border_radius=8,
            label="Mes",
            label_style=ft.TextStyle(size=10, color=COLORS["text_gray"])
        )
        # Asignación de evento explícita
        self.month_dropdown.on_change = self._on_month_changed
        self.month_dropdown.text_style = ft.TextStyle(color=COLORS["text_black"], weight=ft.FontWeight.BOLD)

        return ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon("access_time", size=16, color=COLORS["text_gray"]),
                        ft.Text("NAVEGACIÓN HISTÓRICA", color=COLORS["text_gray"], size=10, weight=ft.FontWeight.BOLD),
                    ]
                ),
                ft.Row(
                    spacing=15,
                    controls=[self.year_dropdown, self.month_dropdown]
                )
            ]
        )

    def _build_timeline_decoration(self):
        """Pequeña decoración visual de línea de tiempo."""
        return ft.Container(
            height=40,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=2, height=40, bgcolor=COLORS["border_light"]),
                ]
            )
        )

    def _build_title_section(self):
        """Título principal."""
        return ft.Column(
            spacing=5,
            controls=[
                ft.Text("Archivo Histórico", size=28, weight=ft.FontWeight.BOLD, color=COLORS["text_black"]),
                ft.Row(
                    controls=[
                        ft.Icon("verified", color=COLORS["primary"], size=16),
                        ft.Text("Datos Consolidados Oficiales", color=COLORS["text_gray"], size=12),
                    ]
                ),
            ]
        )

    def _build_controls_section(self):
        """Tabs y filtros adicionales."""
        return ft.Column(
            spacing=15,
            controls=[
                # Selector Metrópolis (Visual)
                ft.Container(
                    bgcolor=COLORS["bg_light"],
                    border_radius=10,
                    padding=10,
                    content=ft.Row(
                        controls=[
                            ft.Icon("location_city", size=16, color=COLORS["text_dark_gray"]),
                            ft.Text("València Ciudad", size=12, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Icon("arrow_drop_down", size=16),
                        ]
                    )
                ),
                # Tabs
                ft.Row(
                    scroll=ft.ScrollMode.HIDDEN,
                    spacing=10,
                    controls=[
                        UIElements.create_tab("Calidad Aire", True),
                        UIElements.create_tab("Clima", False),
                        UIElements.create_tab("Movilidad", False),
                    ]
                )
            ]
        )

    def _build_stats_section(self):
        """Sección dinámica de estadísticas."""
        return ft.Container(
            content=ft.Column(
                spacing=15,
                controls=[
                    ft.Text("ESTADÍSTICAS MENSUALES", size=11, weight=ft.FontWeight.BOLD, color=COLORS["text_gray"]),
                    self.stats_column # Aquí se inyectarán las tarjetas
                ]
            )
        )

    def _build_snapshot_section(self):
        """Placeholder para futuro gráfico/snapshot."""
        return ft.Container(
            height=120,
            bgcolor="#e0f7fa", # Color suave cian
            border_radius=15,
            padding=20,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon("insert_chart_outlined", color="#006064", size=30),
                    ft.Text("Tendencia Mensual", color="#006064", size=12, weight=ft.FontWeight.BOLD)
                ]
            )
        )

    def _build_events_section(self):
        """Eventos destacados."""
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("IMPACTO DE EVENTOS", size=11, weight=ft.FontWeight.BOLD, color=COLORS["text_gray"]),
                ft.Row(
                    scroll=ft.ScrollMode.HIDDEN,
                    controls=[
                        self._create_mini_event_card("Fallas", "Alta", COLORS["event_danger"]),
                        self._create_mini_event_card("Tráfico", "Medio", COLORS["traffic"]),
                    ]
                )
            ]
        )

    def _create_mini_event_card(self, title, impact, color):
        return ft.Container(
            bgcolor=COLORS["bg_light"],
            padding=10,
            border_radius=8,
            content=ft.Row(
                controls=[
                    ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
                    ft.Text(title, size=11, weight=ft.FontWeight.BOLD),
                    ft.Text(impact, size=10, color=COLORS["text_gray"]),
                ]
            )
        )

    def _build_reliability_section(self):
        """Índice de completitud de datos."""
        return ft.Container(
            bgcolor=COLORS["bg_light"],
            border_radius=15,
            padding=20,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("CALIDAD DEL DATO", size=10, color=COLORS["text_gray"], weight=ft.FontWeight.BOLD),
                    self.completeness_text,
                    ft.Text("Registros válidos procesados", size=10, color=COLORS["text_gray"]),
                ]
            )
        )

    # --- Lógica de Negocio y Eventos ---

    def _on_year_changed(self, e):
        """Maneja el cambio de año."""
        if not e.control.value: return
        print(f"📅 Año cambiado a: {e.control.value}")
        self.current_year = int(e.control.value)
        self.load_historical_data()

    def _on_month_changed(self, e):
        """Maneja el cambio de mes."""
        if not e.control.value: return
        print(f"📅 Mes cambiado a: {e.control.value}")
        self.current_month = int(e.control.value)
        self.load_historical_data()

    def load_historical_data(self):
        """Orquesta la carga de datos."""
        try:
            from utils.historical_data_processor import HistoricalDataProcessor
            
            print(f"🔄 Cargando datos para: {self.current_year}-{self.current_month:02d}")
            
            # 1. Intentar cargar consolidado
            path = "valencia_pollution_consolidated.csv"
            used_sample = False
            
            if os.path.exists(path):
                processor = HistoricalDataProcessor(path)
                # Cargar solo el slice necesario
                has_data = processor.load_data(year=self.current_year, month=self.current_month)
                
                if has_data:
                    self.historical_stats = processor.calculate_statistics()
                    self.completeness = processor.get_data_completeness()
                else:
                    print("⚠️ No hay datos para esta fecha en el histórico.")
                    used_sample = True
            else:
                print("⚠️ Archivo consolidado no encontrado.")
                used_sample = True
            
            if used_sample:
                self._load_sample_data()
            
            if not self.historical_stats and not used_sample:
                 print("⚠️ Datos cargados pero vacíos.")
                 self._load_sample_data()

            # 2. Actualizar UI
            self._update_view()

        except Exception as e:
            print(f"❌ Error crítico cargando datos: {e}")
            import traceback
            traceback.print_exc()
            self._load_sample_data()
            self._update_view()

    def _load_sample_data(self):
        """Carga datos ficticios si falla lo real."""
        print("⚠️ Usando datos de ejemplo/fallback.")
        self.historical_stats = {
            'NO2': {'avg': 0.0, 'max': 0.0, 'min': 0.0, 'count': 0},
            'O3': {'avg': 0.0, 'max': 0.0, 'min': 0.0, 'count': 0},
            'PM10': {'avg': 0.0, 'max': 0.0, 'min': 0.0, 'count': 0},
        }
        self.completeness = 0.0

    def _update_view(self):
        """Actualiza los componentes visuales con el estado actual."""
        try:
            # 1. Actualizar texto de completitud
            self.completeness_text.value = f"{self.completeness:.1f}%"
            
            # 2. Regenerar tarjetas de estadísticas
            self.stats_column.controls = self._generate_stat_cards()
            
            # 3. Forzar repintado de la página
            if self._page_ref:
                self._page_ref.update()
                print("✅ Vista actualizada correctamente.")
            
        except Exception as e:
            print(f"❌ Error actualizando vista: {e}")

    def _generate_stat_cards(self):
        """Genera la lista de controles para las tarjetas."""
        cards = []
        pollutants = ['NO2', 'O3', 'PM10']
        
        # Colores
        colors = {
            'NO2': COLORS["no2"],
            'O3': COLORS["pollution"], 
            'PM10': COLORS["event_danger"]
        }

        has_data = False
        for p in pollutants:
            if p in self.historical_stats:
                data = self.historical_stats[p]
                if data['count'] > 0:
                    has_data = True
                    cards.append(self._create_single_stat_card(p, data, colors.get(p, COLORS["primary"])))

        if not has_data:
            return [
                ft.Container(
                    padding=20, 
                    content=ft.Text("Sin datos registrados para este periodo", italic=True, color=COLORS["text_gray"])
                )
            ]
        
        return cards

    def _create_single_stat_card(self, name, data, color):
        """Crea una tarjeta individual."""
        return ft.Container(
            bgcolor=COLORS["bg_light"],
            border_radius=10,
            padding=15,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    # Izquierda: Nombre y Promedio
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(name, size=12, weight=ft.FontWeight.BOLD, color=color),
                            ft.Text(f"{data['avg']:.1f} µg/m³", size=20, weight=ft.FontWeight.BOLD),
                        ]
                    ),
                    # Derecha: Min/Max
                    ft.Column(
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Text(f"Max: {data['max']:.0f}", size=10, color=COLORS["text_dark_gray"]),
                            ft.Text(f"Min: {data['min']:.0f}", size=10, color=COLORS["text_gray"]),
                            ft.Text(f"Reg: {data['count']}", size=9, color=COLORS["text_light_gray"]),
                        ]
                    )
                ]
            )
        )
