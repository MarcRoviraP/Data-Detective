"""
Panel lateral izquierdo con capas de inteligencia y nodos de detección.
"""

import flet as ft
from config.theme import COLORS
from .ui_elements import UIElements
from datetime import datetime


class LeftPanel(ft.Container):
    """Panel lateral izquierdo con capas de inteligencia y nodos activos."""
    
    def __init__(self, page: ft.Page = None, on_layer_change=None):
        self._page_ref = page
        self.on_layer_change = on_layer_change  # Callback para notificar cambios de capa
        self.active_layer = "Precipitaciones"  # Capa activa por defecto
        self.nodes_column_ref = ft.Ref[ft.Column]()
        self.last_update_ref = ft.Ref[ft.Text]()
        
        # Referencias para los layer items
        self.layer_refs = {}
        
        super().__init__(
            width=280,
            bgcolor=COLORS["background_dark"],
            padding=20,
            content=self._create_content()
        )
        
        # Cargar datos iniciales
        if self._page_ref:
            self.load_sensor_data()
    
    def _create_content(self):
        """Crea el contenido del panel izquierdo."""
        return ft.Column(
            spacing=20,
            controls=[
                self._create_header(),
                self._create_live_indicator(),
                ft.Divider(height=20, color=COLORS["panel_medium"]),
                self._create_intelligence_layers(),
                ft.Divider(height=40, color=COLORS["panel_medium"]),
                self._create_detection_nodes(),
            ]
        )
    
    def _create_header(self):
        """Crea el header del panel."""
        return ft.Row([
            ft.Icon(ft.icons.Icons.RADAR, color=COLORS["primary"], size=30),
            ft.Column(
                spacing=0,
                controls=[
                    ft.Text(
                        "DATA DETECTIVE / VLC URBAN",
                        color=COLORS["primary"],
                        size=12,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "INTEL",
                        color=COLORS["primary"],
                        size=10,
                        italic=True,
                    ),
                ]
            )
        ])
    
    def _create_live_indicator(self):
        """Crea el indicador LIVE."""
        return ft.Column(
            spacing=5,
            controls=[
                ft.Container(
                    bgcolor=COLORS["panel_medium"],
                    border_radius=20,
                    padding=ft.padding.symmetric(horizontal=15, vertical=8),
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Container(
                                width=8,
                                height=8,
                                bgcolor=COLORS["primary"],
                                border_radius=4,
                            ),
                            ft.Text(
                                "AVAMET + GVA LIVE",
                                color=COLORS["text_white"],
                                size=11,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text("MODE", color=COLORS["text_gray"], size=10),
                        ]
                    )
                ),
                ft.Text(
                    ref=self.last_update_ref,
                    value="Última actualización: --:--",
                    color=COLORS["text_gray"],
                    size=9,
                    italic=True,
                ),
            ]
        )
    
    def _on_layer_click(self, e, layer_name):
        """Maneja el click en una capa de inteligencia."""
        self.active_layer = layer_name
        self._update_layer_ui()
        
        # Notificar al MapContainer
        if self.on_layer_change:
            self.on_layer_change(layer_name)
    
    def _update_layer_ui(self):
        """Actualiza la UI de las capas según la selección activa."""
        for layer_name, layer_ref in self.layer_refs.items():
            is_active = layer_name == self.active_layer
            layer_ref.current.bgcolor = COLORS["panel_medium"] if is_active else "transparent"
            
            # Actualizar controles internos
            row = layer_ref.current.content
            row.controls[1].color = COLORS[self._get_layer_color(layer_name)] if is_active else "#555555"
            row.controls[2].color = COLORS["text_white"] if is_active else COLORS["text_dark_gray"]
            row.controls[4].bgcolor = COLORS[self._get_layer_color(layer_name)] if is_active else "transparent"
        
        if self._page_ref:
            self._page_ref.update()
    
    def _get_layer_color(self, layer_name):
        """Obtiene el color asociado a una capa."""
        colors_map = {
            "Precipitaciones": "precipitation",
            "Contaminación (NO2)": "no2",
            "Contaminación (O3, PM10)": "pollution",
            "Flujo Tráfico DGT": "traffic"
        }
        return colors_map.get(layer_name, "primary")
    
    def _create_intelligence_layers(self):
        """Crea la sección de capas de inteligencia."""
        layers = [
            ("Precipitaciones", ft.icons.Icons.WATER_DROP, COLORS["precipitation"]),
            ("Contaminación (NO2)", ft.icons.Icons.CLOUD, COLORS["no2"]),
            ("Contaminación (O3, PM10)", ft.icons.Icons.BLUR_ON, COLORS["pollution"]),
            ("Flujo Tráfico DGT", ft.icons.Icons.TRAFFIC, COLORS["traffic"]),
        ]
        
        layer_controls = []
        for layer_name, icon, color in layers:
            is_active = layer_name == self.active_layer
            layer_ref = ft.Ref[ft.Container]()
            self.layer_refs[layer_name] = layer_ref
            
            layer_item = ft.Container(
                ref=layer_ref,
                bgcolor=COLORS["panel_medium"] if is_active else "transparent",
                border_radius=10,
                padding=12,
                on_click=lambda e, name=layer_name: self._on_layer_click(e, name),
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Container(
                            width=8,
                            height=8,
                            bgcolor=color,
                            border_radius=4,
                        ),
                        ft.Icon(icon, color=color if is_active else "#555555", size=18),
                        ft.Text(
                            layer_name,
                            color=COLORS["text_white"] if is_active else COLORS["text_dark_gray"],
                            size=13,
                        ),
                        ft.Container(expand=True),
                        ft.Container(
                            width=8,
                            height=8,
                            bgcolor=color if is_active else "transparent",
                            border_radius=4,
                        ),
                    ]
                )
            )
            layer_controls.append(layer_item)
        
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text(
                    "CAPAS DE INTELIGENCIA",
                    color=COLORS["text_gray"],
                    size=10,
                    weight=ft.FontWeight.BOLD,
                ),
                *layer_controls
            ]
        )
    
    def _create_detection_nodes(self):
        """Crea la sección de nodos de detección activos."""
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text(
                    "NODOS DE DETECCIÓN ACTIVOS",
                    color=COLORS["text_gray"],
                    size=10,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Column(
                    ref=self.nodes_column_ref,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.ProgressRing(width=30, height=30, color=COLORS["primary"]),
                                    ft.Text("Cargando datos...", color=COLORS["text_gray"], size=11),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=20,
                        )
                    ]
                ),
            ]
        )
    
    def load_sensor_data(self):
        """Carga datos de sensores en tiempo real."""
        try:
            from utils import get_cached_weather_data, get_cached_air_quality_data, get_cached_traffic_data
            from utils.RealTimeTrafficValencia import get_estado_descripcion
            
            weather_data = get_cached_weather_data()
            air_quality_data = get_cached_air_quality_data()
            traffic_data = get_cached_traffic_data()
            
            nodes = []
            
            # Agregar datos meteorológicos destacados (primeras 2 estaciones con precipitación)
            precip_stations = []
            for c in weather_data:
                if c.prec and c.prec != "-":
                    try:
                        prec_val = float(c.prec.replace(',', '.'))
                        if prec_val > 0:
                            precip_stations.append(c)
                    except:
                        pass
            precip_stations = precip_stations[:2]
            
            if not precip_stations:
                precip_stations = weather_data[:2]
            
            for clima in precip_stations:
                if clima.tmed and clima.tmed != "-":
                    # Determinar si hay alerta por precipitación
                    alert_color = COLORS["primary"]
                    if clima.prec and clima.prec != "-":
                        try:
                            prec_val = float(clima.prec.replace(',', '.'))
                            if prec_val > 10:
                                alert_color = COLORS["event_danger"]
                            elif prec_val > 5:
                                alert_color = COLORS["traffic"]
                        except:
                            pass
                    
                    nodes.append(
                        self._create_enhanced_node_card(
                            f"☔ {clima.estacion[:18]}",
                            f"{clima.tmed}°C",
                            alert_color,
                            ft.icons.Icons.WATER_DROP,
                            f"💧 {clima.prec}mm" if clima.prec != "-" else "Sin lluvia",
                            f"💨 {clima.hr}%" if clima.hr != "-" else ""
                        )
                    )
            
            # Agregar datos de calidad del aire (estaciones con peor calidad)
            no2_stations = sorted(
                [e for e in air_quality_data if e.no2 and e.no2 != "-"],
                key=lambda x: float(x.no2) if x.no2 != "-" else 0,
                reverse=True
            )[:2]
            
            for estacion in no2_stations:
                # Determinar color según nivel de NO2
                alert_color = COLORS["no2"]
                try:
                    no2_val = float(estacion.no2)
                    if no2_val > 200:
                        alert_color = COLORS["event_danger"]
                    elif no2_val > 100:
                        alert_color = COLORS["traffic"]
                except:
                    pass
                
                nodes.append(
                    self._create_enhanced_node_card(
                        f"🌫️ {estacion.direccion[:18]}",
                        f"{estacion.no2} μg/m³",
                        alert_color,
                        ft.icons.Icons.CLOUD,
                        f"NO2",
                        estacion.calidad_am if estacion.calidad_am != "-" else ""
                    )
                )
            
            # Agregar datos de tráfico (estaciones con problemas)
            traffic_alerts = []
            for t in traffic_data:
                estado_desc, color_sugerido = get_estado_descripcion(t.estado)
                if color_sugerido in ["yellow", "red"]:  # Solo denso, congestionado o cortado
                    traffic_alerts.append((t, estado_desc, color_sugerido))
            
            # Mostrar primeras 2 alertas de tráfico
            for t, estado_desc, color_sugerido in traffic_alerts[:2]:
                color_map = {
                    "green": COLORS["primary"],
                    "yellow": COLORS["traffic"],
                    "red": COLORS["event_danger"],
                    "gray": COLORS["text_gray"]
                }
                alert_color = color_map.get(color_sugerido, COLORS["traffic"])
                
                nodes.append(
                    self._create_enhanced_node_card(
                        f"🚦 {t.denominacion[:18]}",
                        estado_desc,
                        alert_color,
                        ft.icons.Icons.TRAFFIC,
                        f"🚗 {t.intensidad} v/h" if t.intensidad != "-" else "",
                        f"⚡ {t.velocidad} km/h" if t.velocidad != "-" else ""
                    )
                )
            
            # Si no hay suficientes nodos, agregar sensores normales
            if len(nodes) < 4:
                # Agregar más estaciones meteorológicas
                for clima in weather_data[len(precip_stations):4]:
                    if clima.tmed and clima.tmed != "-":
                        nodes.append(
                            self._create_enhanced_node_card(
                                f"🌡️ {clima.estacion[:18]}",
                                f"{clima.tmed}°C",
                                COLORS["primary"],
                                ft.icons.Icons.THERMOSTAT,
                                f"💨 {clima.hr}%" if clima.hr != "-" else "",
                                ""
                            )
                        )
                    if len(nodes) >= 6:
                        break
            
            # Limitar a 6 nodos para no saturar
            nodes = nodes[:6]
            
            # Si aún no hay datos, mostrar mensaje
            if not nodes:
                nodes = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.icons.Icons.SENSORS_OFF, color=COLORS["text_gray"], size=40),
                                ft.Text("No hay datos disponibles", color=COLORS["text_gray"], size=11),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=20,
                    )
                ]
            
            # Actualizar UI
            if self.nodes_column_ref.current:
                self.nodes_column_ref.current.controls = nodes
            
            # Actualizar timestamp
            if self.last_update_ref.current:
                now = datetime.now().strftime("%H:%M:%S")
                self.last_update_ref.current.value = f"Última actualización: {now}"
            
            if self._page_ref:
                self._page_ref.update()
                
        except Exception as e:
            print(f"❌ Error al cargar datos de sensores: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_enhanced_node_card(self, title, value, color, icon, detail1="", detail2=""):
        """Crea una tarjeta de nodo mejorada con más información."""
        details = []
        if detail1:
            details.append(
                ft.Text(detail1, color=COLORS["text_gray"], size=9)
            )
        if detail2:
            details.append(
                ft.Text(detail2, color=COLORS["text_gray"], size=9)
            )
        
        return ft.Container(
            bgcolor=COLORS["panel_medium"],
            border_radius=10,
            padding=12,
            border=ft.border.all(1, color + "44"),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=color, size=16),
                            ft.Text(
                                title,
                                color=COLORS["text_white"],
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                            ),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=3,
                                height=20,
                                bgcolor=color,
                                border_radius=2,
                            ),
                            ft.Text(
                                value,
                                color=color,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ]
                    ),
                    *([ft.Row(
                        spacing=8,
                        controls=details
                    )] if details else [])
                ]
            )
        )
