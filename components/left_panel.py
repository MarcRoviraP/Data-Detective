"""
Panel lateral izquierdo con capas de inteligencia y nodos de detección.
"""

import flet as ft
from config.theme import COLORS
from .ui_elements import UIElements


class LeftPanel(ft.Container):
    """Panel lateral izquierdo con capas de inteligencia y nodos activos."""
    
    def __init__(self):
        super().__init__(
            width=280,
            bgcolor=COLORS["background_dark"],
            padding=20,
            content=self._create_content()
        )
    
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
        return ft.Container(
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
        )
    
    def _create_intelligence_layers(self):
        """Crea la sección de capas de inteligencia."""
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text(
                    "CAPAS DE INTELIGENCIA",
                    color=COLORS["text_gray"],
                    size=10,
                    weight=ft.FontWeight.BOLD,
                ),
                UIElements.create_layer_item(
                    "Precipitaciones",
                    ft.icons.Icons.WATER_DROP,
                    COLORS["precipitation"],
                    True
                ),
                UIElements.create_layer_item(
                    "Contaminación (NO2)",
                    ft.icons.Icons.CLOUD,
                    COLORS["no2"],
                    False
                ),
                UIElements.create_layer_item(
                    "Contaminación (O3, PM10)",
                    ft.icons.Icons.BLUR_ON,
                    COLORS["pollution"],
                    False
                ),
                UIElements.create_layer_item(
                    "Flujo Tráfico DGT",
                    ft.icons.Icons.TRAFFIC,
                    COLORS["traffic"],
                    False
                ),
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
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    controls=[
                        UIElements.create_node_card(
                            "AVAMET | VLC-01",
                            "22.8°C",
                            COLORS["primary"],
                            ft.icons.Icons.THERMOSTAT,
                            "82%"
                        ),
                        UIElements.create_node_card(
                            "GVA | NO2 NODO",
                            "18 μg/m³",
                            COLORS["no2"],
                            ft.icons.Icons.CO2,
                            "45%"
                        ),
                        UIElements.create_node_card(
                            "DGT | V-30 INTEL",
                            "84% FLUX",
                            COLORS["traffic"],
                            ft.icons.Icons.DIRECTIONS_CAR,
                            "AC"
                        ),
                        UIElements.create_node_card(
                            "GVA | RUZAFA-S",
                            "58 dB",
                            COLORS["pollution"],
                            ft.icons.Icons.VOLUME_UP,
                            "94%"
                        ),
                    ]
                ),
            ]
        )
