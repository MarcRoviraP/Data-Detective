"""
Contenedor del mapa central con selector de capas.
"""

import flet as ft
import flet_map as mapa
from config.map_styles import MAP_STYLES
from config.theme import COLORS


class MapContainer(ft.Container):
    """Contenedor del mapa central con selector de capas y controles."""
    
    def __init__(self):
        self.current_map_style = "Normal"
        self.map_style_buttons_refs = {}
        
        # Referencias para las capas
        self.tile_layer_ref = ft.Ref[mapa.TileLayer]()
        self.marker_layer_ref = ft.Ref[mapa.MarkerLayer]()
        
        super().__init__(
            expand=True,
            content=self._create_content()
        )
    
    def _create_content(self):
        """Crea el contenido del mapa."""
        return ft.Stack(
            controls=[
                self._create_map(),
                self._create_layer_selector(),
                self._create_footer(),
            ]
        )
    
    def _create_map(self):
        """Crea el componente del mapa."""
        return mapa.Map(
            expand=True,
            initial_center=mapa.MapLatitudeLongitude(39.4699, -0.3763),
            initial_zoom=12,
            interaction_configuration=mapa.InteractionConfiguration(
                flags=mapa.InteractionFlag.ALL
            ),
            layers=[
                mapa.TileLayer(
                    ref=self.tile_layer_ref,
                    url_template=MAP_STYLES[self.current_map_style],
                ),
                mapa.MarkerLayer(ref=self.marker_layer_ref, markers=[]),
            ],
        )
    
    def _create_layer_selector(self):
        """Crea el selector de capas de mapa."""
        # Crear botones y guardar sus referencias
        capas = [
            self._create_map_style_button("Normal", ft.icons.Icons.MAP),
            self._create_map_style_button("Satélite", ft.icons.Icons.SATELLITE),
            self._create_map_style_button("Oscuro", ft.icons.Icons.DARK_MODE),
            self._create_map_style_button("Topográfico", ft.icons.Icons.TERRAIN)
        ]
        
        return ft.Container(
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
                            color=COLORS["text_gray"],
                            size=10,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Column(
                            spacing=5,
                            controls=capas
                        )
                    ]
                )
            )
        )
    
    def _create_map_style_button(self, style_name, icon):
        """Crea un botón para cambiar el estilo del mapa."""
        is_active = self.current_map_style == style_name
        
        # Crear referencias para cada elemento del botón
        container_ref = ft.Ref[ft.Container]()
        icon_ref = ft.Ref[ft.Icon]()
        text_ref = ft.Ref[ft.Text]()
        
        button = ft.Container(
            ref=container_ref,
            bgcolor=COLORS["primary"] if is_active else COLORS["panel_dark"],
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(
                        ref=icon_ref,
                        icon=icon,
                        color=COLORS["text_black"] if is_active else COLORS["text_gray"],
                        size=16
                    ),
                    ft.Text(
                        ref=text_ref,
                        value=style_name,
                        color=COLORS["text_black"] if is_active else COLORS["text_white"],
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
        """Cambia el estilo del mapa."""
        print(f"🗺️ Cambiando a: {style_name}")
        
        self.current_map_style = style_name
        self.tile_layer_ref.current.url_template = MAP_STYLES[style_name]
        
        # Actualizar todos los botones usando las referencias guardadas
        for btn_name, refs in self.map_style_buttons_refs.items():
            is_active = btn_name == style_name
            
            # Actualizar el container (fondo)
            refs["container"].current.bgcolor = COLORS["primary"] if is_active else COLORS["panel_dark"]
            
            # Actualizar el icono
            refs["icon"].current.color = COLORS["text_black"] if is_active else COLORS["text_gray"]
            
            # Actualizar el texto
            refs["text"].current.color = COLORS["text_black"] if is_active else COLORS["text_white"]
            refs["text"].current.weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL
        
        self.update()
        print(f"✅ Mapa actualizado a {style_name}")
    
    def _create_footer(self):
        """Crea el footer con fuente de datos."""
        return ft.Container(
            bottom=20,
            left=20,
            content=ft.Text(
                "Source: AVAMET & GVA OpenData",
                color=COLORS["primary"],
                size=10,
            )
        )
