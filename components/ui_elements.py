"""
Elementos UI reutilizables para Data Detective.
"""

import flet as ft
from config.theme import COLORS


class UIElements:
    """Clase con métodos estáticos para crear elementos UI reutilizables."""
    
    @staticmethod
    def create_layer_item(text, icon, color, is_active):
        """Crea un item de capa de inteligencia."""
        return ft.Container(
            bgcolor=COLORS["panel_medium"] if is_active else "transparent",
            border_radius=10,
            padding=12,
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
                        text,
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
    
    @staticmethod
    def create_node_card(title, value, color, icon, percentage):
        """Crea una tarjeta de nodo de detección."""
        return ft.Container(
            bgcolor=COLORS["panel_dark"],
            border_radius=15,
            padding=15,
            border=ft.border.all(1, COLORS["panel_medium"]),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=color, size=16),
                            ft.Text(
                                title,
                                color=COLORS["text_gray"],
                                size=11,
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                percentage,
                                color=color,
                                size=11,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ]
                    ),
                    ft.Text(
                        value,
                        color=color,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                ]
            )
        )
    
    @staticmethod
    def create_tab(text, is_active):
        """Crea un tab de categoría."""
        return ft.Container(
            bgcolor=COLORS["text_black"] if is_active else "transparent",
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            content=ft.Row(
                spacing=5,
                controls=[
                    ft.Icon(
                        ft.icons.Icons.CIRCLE,
                        size=8,
                        color=COLORS["primary"] if is_active else COLORS["text_light_gray"]
                    ),
                    ft.Text(
                        text,
                        color=COLORS["text_white"] if is_active else COLORS["text_dark_gray"],
                        size=12,
                    ),
                ]
            )
        )
    
    @staticmethod
    def create_event_card(title, percentage, subtitle, color, image_url):
        """Crea una tarjeta de evento."""
        return ft.Container(
            width=180,
            border_radius=15,
            bgcolor=COLORS["bg_light"],
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=120,
                        bgcolor=COLORS["text_light_gray"],
                        border_radius=ft.border_radius.only(top_left=15, top_right=15),
                    ),
                    ft.Container(
                        padding=15,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(
                                    title,
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            f"Picos de NO2: {percentage}",
                                            size=10,
                                            color=color,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ]
                                ),
                                ft.Text(
                                    subtitle,
                                    size=9,
                                    color=COLORS["text_gray"],
                                ),
                            ]
                        )
                    ),
                ]
            )
        )
    
    @staticmethod
    def create_source_badge(text):
        """Crea un badge de fuente de datos."""
        return ft.Container(
            bgcolor=COLORS["bg_white"],
            border=ft.border.all(1, COLORS["border_light"]),
            border_radius=8,
            padding=10,
            content=ft.Text(
                text,
                size=10,
                color=COLORS["text_dark_gray"],
                text_align=ft.TextAlign.CENTER,
            )
        )
