"""
Panel lateral derecho con archivo histórico y análisis.
"""

import flet as ft
from config.theme import COLORS
from .ui_elements import UIElements


class RightPanel(ft.Container):
    """Panel lateral derecho con archivo histórico y datos consolidados."""
    
    def __init__(self):
        super().__init__(
            width=400,
            bgcolor=COLORS["bg_white"],
            padding=30,
            content=self._create_content()
        )
    
    def _create_content(self):
        """Crea el contenido del panel derecho."""
        return ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self._create_year_header(),
                self._create_timeline(),
                self._create_archive_title(),
                self._create_metropolis_selector(),
                self._create_category_tabs(),
                self._create_density_section(),
                self._create_map_snapshot(),
                self._create_events_section(),
                self._create_reliability_index(),
            ]
        )
    
    def _create_year_header(self):
        """Crea el header del año."""
        return ft.Column(
            spacing=5,
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("AÑO", color=COLORS["text_gray"], size=12),
                    ]
                ),
                ft.Text("2023", color=COLORS["text_light_gray"], size=14),
            ]
        )
    
    def _create_timeline(self):
        """Crea la línea de tiempo vertical."""
        return ft.Container(
            height=150,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        width=2,
                        height=50,
                        bgcolor=COLORS["border_light"],
                    ),
                    ft.Container(
                        width=12,
                        height=12,
                        bgcolor=COLORS["text_black"],
                        border_radius=6,
                    ),
                    ft.Text("1950", size=10, color=COLORS["text_gray"]),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
    
    def _create_archive_title(self):
        """Crea el título del archivo histórico."""
        return ft.Column(
            spacing=5,
            controls=[
                ft.Text(
                    "Archivo Histórico",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=COLORS["text_black"],
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.icons.Icons.VERIFIED, color=COLORS["no2"], size=16),
                        ft.Text(
                            "Data Detective Verified",
                            color=COLORS["text_gray"],
                            size=11,
                        ),
                    ]
                ),
                ft.Text(
                    "Datasets consolidados: 1950 - 2023",
                    color=COLORS["text_dark_gray"],
                    size=13,
                ),
            ]
        )
    
    def _create_metropolis_selector(self):
        """Crea el selector de metrópolis."""
        return ft.Container(
            bgcolor=COLORS["bg_light"],
            border_radius=10,
            padding=15,
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Metrópolis VLC",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(expand=True),
                    ft.Icon(ft.icons.Icons.ARROW_DROP_DOWN, size=20),
                ]
            )
        )
    
    def _create_category_tabs(self):
        """Crea los tabs de categorías."""
        return ft.Row(
            spacing=15,
            controls=[
                UIElements.create_tab("Contaminación", True),
                UIElements.create_tab("Precipitaciones", False),
                UIElements.create_tab("Tráfico", False),
            ]
        )
    
    def _create_density_section(self):
        """Crea la sección de densidad histórica."""
        return ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.icons.Icons.LAYERS, size=16),
                        ft.Text(
                            "DENSIDAD HISTÓRICA:",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ]
                ),
                ft.Text("CONTAMINACIÓN", size=13, weight=ft.FontWeight.BOLD),
                # Escala de color
                ft.Container(
                    height=40,
                    border_radius=10,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.Alignment.CENTER_LEFT,
                        end=ft.alignment.Alignment.CENTER_RIGHT,
                        colors=["#6b4a9e", "#4a7fc9", "#00bfa5", "#7cb342", "#fdd835"],
                    ),
                    content=ft.Row(
                        controls=[
                            ft.Text("MIN", size=10, color=COLORS["text_white"]),
                            ft.Container(expand=True),
                            ft.Text("MAX", size=10, color=COLORS["text_white"]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=10,
                ),
            ]
        )
    
    def _create_map_snapshot(self):
        """Crea el snapshot del mapa."""
        return ft.Container(
            height=200,
            bgcolor="#b0d4d4",
            border_radius=15,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        bgcolor="#b0d4d4",
                        border_radius=15,
                    ),
                    ft.Container(
                        right=15,
                        top=15,
                        content=ft.Container(
                            bgcolor=COLORS["bg_white"],
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("SNAPSHOT", size=8, color=COLORS["text_gray"]),
                                    ft.Text("1982 Edition", size=12, weight=ft.FontWeight.BOLD),
                                ]
                            )
                        )
                    ),
                ]
            )
        )
    
    def _create_events_section(self):
        """Crea la sección de impacto de grandes eventos."""
        return ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            width=12,
                            height=12,
                            bgcolor=COLORS["primary"],
                            border_radius=6,
                        ),
                        ft.Text(
                            "IMPACTO: GRANDES EVENTOS",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ]
                ),
                ft.Text(
                    "IMPACTO HISTÓRICO: CONTAMINACIÓN",
                    size=10,
                    color=COLORS["text_gray"],
                ),
                ft.Row(
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        UIElements.create_event_card(
                            "Les Falles",
                            "+180%",
                            "(Mascleta)",
                            COLORS["event_danger"],
                            "https://via.placeholder.com/150"
                        ),
                        UIElements.create_event_card(
                            "Nadal VLC",
                            "+45%",
                            "(Centre)",
                            COLORS["event_success"],
                            "https://via.placeholder.com/150"
                        ),
                    ]
                ),
            ]
        )
    
    def _create_reliability_index(self):
        """Crea el índice de fiabilidad de datos."""
        return ft.Container(
            bgcolor=COLORS["bg_light"],
            border_radius=15,
            padding=20,
            content=ft.Column(
                spacing=15,
                controls=[
                    ft.Text(
                        "HISTORICAL DATA INDEX",
                        size=10,
                        color=COLORS["text_gray"],
                    ),
                    ft.Text(
                        "Repositorio València",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Row(
                        spacing=20,
                        controls=[
                            UIElements.create_source_badge("GVA\nPortal"),
                            UIElements.create_source_badge("DGT\nIntel"),
                            UIElements.create_source_badge("AEMET\nOpen"),
                        ]
                    ),
                    # Gráfico circular de fiabilidad
                    ft.Container(
                        width=150,
                        height=150,
                        content=ft.Stack(
                            controls=[
                                ft.Container(
                                    width=150,
                                    height=150,
                                    border_radius=75,
                                    bgcolor=COLORS["border_light"],
                                ),
                                ft.Container(
                                    alignment=ft.alignment.Alignment.CENTER,
                                    content=ft.Column(
                                        alignment=ft.alignment.Alignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text(
                                                "88%",
                                                size=40,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.Container(
                                                bgcolor=COLORS["primary"],
                                                border_radius=12,
                                                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                                content=ft.Text(
                                                    "FIABILIDAD DATA",
                                                    size=8,
                                                    color=COLORS["text_black"],
                                                    weight=ft.FontWeight.BOLD,
                                                )
                                            ),
                                        ]
                                    )
                                ),
                            ]
                        )
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
