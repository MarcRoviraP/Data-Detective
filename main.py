import flet as ft
import flet_map as mapa
from datetime import datetime


class DataDetectiveUI(ft.Row):
    def __init__(self):
        super().__init__(spacing=0, expand=True)
        self.map_style_buttons_refs = {}

        # Referencias para el mapa
        self.marker_layer_ref = ft.Ref[mapa.MarkerLayer]()
        
        # Panel lateral izquierdo
        self.left_panel = self.create_left_panel()
        
        # Mapa central
        self.map_container = self.create_map_container()
        
        # Panel lateral derecho
        self.right_panel = self.create_right_panel()
        
        self.controls = [
            self.left_panel,
            self.map_container,
            self.right_panel,
        ]
    
    def create_left_panel(self):
        """Panel lateral izquierdo con capas de inteligencia y nodos"""
        return ft.Container(
            width=280,
            bgcolor="#0a0e1a",
            padding=20,
            content=ft.Column(
                spacing=20,
                controls=[
                    # Header
                    ft.Row([
                        ft.Icon(ft.icons.Icons.RADAR, color="#00ff88", size=30),
                        ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text(
                                    "DATA DETECTIVE / VLC URBAN",
                                    color="#00ff88",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "INTEL",
                                    color="#00ff88",
                                    size=10,
                                    italic=True,
                                ),
                            ]
                        )
                    ]),
                    
                    # Indicador LIVE
                    ft.Container(
                        bgcolor="#1a2332",
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        content=ft.Row(
                            spacing=8,
                            controls=[
                                ft.Container(
                                    width=8,
                                    height=8,
                                    bgcolor="#00ff88",
                                    border_radius=4,
                                ),
                                ft.Text(
                                    "AVAMET + GVA LIVE",
                                    color="white",
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text("MODE", color="#888888", size=10),
                            ]
                        )
                    ),
                    
                    ft.Divider(height=20, color="#1a2332"),
                    
                    # Capas de Inteligencia
                    ft.Text(
                        "CAPAS DE INTELIGENCIA",
                        color="#888888",
                        size=10,
                        weight=ft.FontWeight.BOLD,
                    ),
                    
                    self.create_layer_item(
                        "Precipitaciones",
                        ft.icons.Icons.WATER_DROP,
                        "#00ff88",
                        True
                    ),
                    self.create_layer_item(
                        "Contaminación (NO2)",
                        ft.icons.Icons.CLOUD,
                        "#4a9eff",
                        False
                    ),
                    self.create_layer_item(
                        "Contaminación (O3, PM10)",
                        ft.icons.Icons.BLUR_ON,
                        "#9b4aff",
                        False
                    ),
                    self.create_layer_item(
                        "Flujo Tráfico DGT",
                        ft.icons.Icons.TRAFFIC,
                        "#ffaa00",
                        False
                    ),
                    
                    ft.Divider(height=40, color="#1a2332"),
                    
                    # Nodos de Detección Activos
                    ft.Text(
                        "NODOS DE DETECCIÓN ACTIVOS",
                        color="#888888",
                        size=10,
                        weight=ft.FontWeight.BOLD,
                    ),
                    
                    ft.Column(
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                        controls=[
                            self.create_node_card(
                                "AVAMET | VLC-01",
                                "22.8°C",
                                "#00ff88",
                                ft.icons.Icons.THERMOSTAT,
                                "82%"
                            ),
                            self.create_node_card(
                                "GVA | NO2 NODO",
                                "18 μg/m³",
                                "#4a9eff",
                                ft.icons.Icons.CO2,
                                "45%"
                            ),
                            self.create_node_card(
                                "DGT | V-30 INTEL",
                                "84% FLUX",
                                "#ffaa00",
                                ft.icons.Icons.DIRECTIONS_CAR,
                                "AC"
                            ),
                            self.create_node_card(
                                "GVA | RUZAFA-S",
                                "58 dB",
                                "#9b4aff",
                                ft.icons.Icons.VOLUME_UP,
                                "94%"
                            ),
                        ]
                    ),
                ]
            )
        )
    
    def create_layer_item(self, text, icon, color, is_active):
        """Crea un item de capa de inteligencia"""
        return ft.Container(
            bgcolor="#1a2332" if is_active else "transparent",
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
                        color="white" if is_active else "#666666",
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
    
    def create_node_card(self, title, value, color, icon, percentage):
        """Crea una tarjeta de nodo de detección"""
        return ft.Container(
            bgcolor="#12171f",
            border_radius=15,
            padding=15,
            border=ft.border.all(1, "#1a2332"),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=color, size=16),
                            ft.Text(
                                title,
                                color="#888888",
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
    def create_map_container(self):
        """Contenedor del mapa central con selector de capas"""
        self.current_map_style = "Normal"

        # Referencias para las capas
        self.tile_layer_ref = ft.Ref[mapa.TileLayer]()

        # Crear botones y guardar sus referencias
        self.capas = [
            self.create_map_style_button("Normal", ft.icons.Icons.MAP),
            self.create_map_style_button("Satélite", ft.icons.Icons.SATELLITE),
            self.create_map_style_button("Oscuro", ft.icons.Icons.DARK_MODE),
            self.create_map_style_button("Topográfico", ft.icons.Icons.TERRAIN)
        ]

        # Estilos de mapa disponibles
        self.map_styles = {
            "Normal": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "Satélite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "Oscuro": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            "Topográfico": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        }

        return ft.Container(
            expand=True,
            content=ft.Stack(
                controls=[
                    # Mapa
                    mapa.Map(
                        expand=True,
                        initial_center=mapa.MapLatitudeLongitude(39.4699, -0.3763),
                        initial_zoom=12,
                        interaction_configuration=mapa.InteractionConfiguration(
                            flags=mapa.InteractionFlag.ALL
                        ),
                        layers=[
                            mapa.TileLayer(
                                ref=self.tile_layer_ref,
                                url_template=self.map_styles[self.current_map_style],
                            ),
                            mapa.MarkerLayer(ref=self.marker_layer_ref, markers=[]),
                        ],
                    ),

                    # Selector de capas (arriba a la izquierda)
                    ft.Container(
                        left=20,
                        top=20,
                        content=ft.Container(
                            bgcolor="#1a2332ee",
                            border_radius=10,
                            padding=10,
                            content=ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Text(
                                        "CAPAS DE MAPA",
                                        color="#888888",
                                        size=10,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Column(
                                        spacing=5,
                                        controls=self.capas
                                    )
                                ]
                            )
                        )
                    ),

                    # Footer con fuente de datos
                    ft.Container(
                        bottom=20,
                        left=20,
                        content=ft.Text(
                            "Source: AVAMET & GVA OpenData",
                            color="#00ff88",
                            size=10,
                        )
                    ),
                ]
            )
        )

    def create_map_style_button(self, style_name, icon):
        """Crea un botón para cambiar el estilo del mapa"""
        is_active = self.current_map_style == style_name

        # Crear referencias para cada elemento del botón
        container_ref = ft.Ref[ft.Container]()
        icon_ref = ft.Ref[ft.Icon]()
        text_ref = ft.Ref[ft.Text]()

        print(style_name, is_active)

        button = ft.Container(
            ref=container_ref,
            bgcolor="#00ff88" if is_active else "#12171f",
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(
                        ref=icon_ref,
                        icon=icon,
                        color="black" if is_active else "#888888",
                        size=16
                    ),
                    ft.Text(
                        ref=text_ref,
                        value=style_name,
                        color="black" if is_active else "white",
                        size=12,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                    ),
                ]
            ),
            on_click=lambda e, style=style_name: self.change_map_style(style),
        )

        # Guardar las referencias en el diccionario
        self.map_style_buttons_refs[style_name] = {
            "container": container_ref,
            "icon": icon_ref,
            "text": text_ref
        }

        return button


    def change_map_style(self, style_name):
        """Cambia el estilo del mapa"""
        print(f"🗺️ Cambiando a: {style_name}")

        self.current_map_style = style_name
        self.tile_layer_ref.current.url_template = self.map_styles[style_name]

        # Actualizar todos los botones usando las referencias guardadas
        for btn_name, refs in self.map_style_buttons_refs.items():
            is_active = btn_name == style_name

            # Actualizar el container (fondo)
            refs["container"].current.bgcolor = "#00ff88" if is_active else "#12171f"

            # Actualizar el icono
            refs["icon"].current.color = "black" if is_active else "#888888"

            # Actualizar el texto
            refs["text"].current.color = "black" if is_active else "white"
            refs["text"].current.weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL

        self.update()
        print(self.current_map_style)
        print(f"✅ Mapa actualizado a {style_name}")
    
    def create_right_panel(self):
        """Panel lateral derecho con archivo histórico"""
        return ft.Container(
            width=400,
            bgcolor="white",
            padding=30,
            content=ft.Column(
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    # Header año
                    ft.Row(
                        controls=[
                            ft.Text("AÑO", color="#888888", size=12),
                        ]
                    ),
                    ft.Text("2023", color="#cccccc", size=14),
                    
                    # Timeline vertical
                    ft.Container(
                        height=150,
                        content=ft.Column(
                            spacing=0,
                            controls=[
                                ft.Container(
                                    width=2,
                                    height=50,
                                    bgcolor="#e0e0e0",
                                ),
                                ft.Container(
                                    width=12,
                                    height=12,
                                    bgcolor="black",
                                    border_radius=6,
                                ),
                                ft.Text("1950", size=10, color="#888888"),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ),
                    
                    # Título archivo histórico
                    ft.Column(
                        spacing=5,
                        controls=[
                            ft.Text(
                                "Archivo Histórico",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color="black",
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.icons.Icons.VERIFIED, color="#4a9eff", size=16),
                                    ft.Text(
                                        "Data Detective Verified",
                                        color="#888888",
                                        size=11,
                                    ),
                                ]
                            ),
                            ft.Text(
                                "Datasets consolidados: 1950 - 2023",
                                color="#666666",
                                size=13,
                            ),
                        ]
                    ),
                    
                    # Selector de metrópolis
                    ft.Container(
                        bgcolor="#f5f5f5",
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
                    ),
                    
                    # Tabs de categorías
                    ft.Row(
                        spacing=15,
                        controls=[
                            self.create_tab("Contaminación", True),
                            self.create_tab("Precipitaciones", False),
                            self.create_tab("Tráfico", False),
                        ]
                    ),
                    
                    # Densidad histórica
                    ft.Column(
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
                                        ft.Text("MIN", size=10, color="white"),
                                        ft.Container(expand=True),
                                        ft.Text("MAX", size=10, color="white"),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                ),
                                padding=10,
                            ),
                        ]
                    ),
                    
                    # Snapshot del mapa
                    ft.Container(
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
                                        bgcolor="white",
                                        border_radius=8,
                                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                        content=ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text("SNAPSHOT", size=8, color="#888888"),
                                                ft.Text("1982 Edition", size=12, weight=ft.FontWeight.BOLD),
                                            ]
                                        )
                                    )
                                ),
                            ]
                        )
                    ),
                    
                    # Impacto grandes eventos
                    ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=12,
                                        height=12,
                                        bgcolor="#00ff88",
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
                                color="#888888",
                            ),
                        ]
                    ),
                    
                    # Tarjetas de eventos
                    ft.Row(
                        spacing=15,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            self.create_event_card(
                                "Les Falles",
                                "+180%",
                                "(Mascleta)",
                                "#ff4444",
                                "https://via.placeholder.com/150"
                            ),
                            self.create_event_card(
                                "Nadal VLC",
                                "+45%",
                                "(Centre)",
                                "#00ff88",
                                "https://via.placeholder.com/150"
                            ),
                        ]
                    ),
                    
                    # Índice de fiabilidad
                    ft.Container(
                        bgcolor="#f5f5f5",
                        border_radius=15,
                        padding=20,
                        content=ft.Column(
                            spacing=15,
                            controls=[
                                ft.Text(
                                    "HISTORICAL DATA INDEX",
                                    size=10,
                                    color="#888888",
                                ),
                                ft.Text(
                                    "Repositorio València",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Row(
                                    spacing=20,
                                    controls=[
                                        self.create_source_badge("GVA\nPortal"),
                                        self.create_source_badge("DGT\nIntel"),
                                        self.create_source_badge("AEMET\nOpen"),
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
                                                bgcolor="#e0e0e0",
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
                                                            bgcolor="#00ff88",
                                                            border_radius=12,
                                                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                                            content=ft.Text(
                                                                "FIABILIDAD DATA",
                                                                size=8,
                                                                color="black",
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
                    ),
                ]
            )
        )
    
    def create_tab(self, text, is_active):
        """Crea un tab de categoría"""
        return ft.Container(
            bgcolor="black" if is_active else "transparent",
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            content=ft.Row(
                spacing=5,
                controls=[
                    ft.Icon(
                        ft.icons.Icons.CIRCLE,
                        size=8,
                        color="#00ff88" if is_active else "#cccccc"
                    ),
                    ft.Text(
                        text,
                        color="white" if is_active else "#666666",
                        size=12,
                    ),
                ]
            )
        )
    
    def create_event_card(self, title, percentage, subtitle, color, image_url):
        """Crea una tarjeta de evento"""
        return ft.Container(
            width=180,
            border_radius=15,
            bgcolor="#f5f5f5",
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=120,
                        bgcolor="#cccccc",
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
                                    color="#888888",
                                ),
                            ]
                        )
                    ),
                ]
            )
        )
    
    def create_source_badge(self, text):
        """Crea un badge de fuente de datos"""
        return ft.Container(
            bgcolor="white",
            border=ft.border.all(1, "#e0e0e0"),
            border_radius=8,
            padding=10,
            content=ft.Text(
                text,
                size=10,
                color="#666666",
                text_align=ft.TextAlign.CENTER,
            )
        )


def main(page: ft.Page):
    page.title = "Data Detective - VLC Urban Intel"
    page.padding = 0
    page.window.maximized = True
    page.bgcolor = "#0a0e1a"
    
    # Agregar la UI principal
    page.add(DataDetectiveUI())


ft.run(main)