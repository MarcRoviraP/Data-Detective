"""
Contenedor del mapa central con selector de capas.
"""

import flet as ft
import flet_map as mapa
from config.map_styles import MAP_STYLES
from config.theme import COLORS


class MapContainer(ft.Container):
    """Contenedor del mapa central con selector de capas y controles."""
    
    def __init__(self, page: ft.Page = None):
        self._page_ref = page
        self.current_map_style = "Normal"
        self.current_layer = "Precipitaciones"  # Capa activa
        self.map_style_buttons_refs = {}
        
        # Referencias para las capas
        self.tile_layer_ref = ft.Ref[mapa.TileLayer]()
        self.marker_layer_ref = ft.Ref[mapa.MarkerLayer]()
        
        # Almacenar todos los marcadores por tipo
        self.all_markers = {
            "Precipitaciones": [],
            "Contaminación (NO2)": [],
            "Contaminación (O3, PM10)": [],
            "Flujo Tráfico DGT": []
        }
        
        # Estado para la tarjeta de información
        self.info_card_ref = ft.Ref[ft.Container]()
        self.selected_marker_data = None
        
        super().__init__(
            expand=True,
            content=self._create_content()
        )
        
        # Cargar marcadores iniciales
        if self._page_ref:
            self.load_markers()
    
    def on_layer_change(self, layer_name):
        """Callback cuando cambia la capa activa."""
        print(f"🔄 Cambiando capa a: {layer_name}")
        self.current_layer = layer_name
        self.update_visible_markers()
    
    def update_visible_markers(self):
        """Actualiza los marcadores visibles según la capa activa."""
        if self.marker_layer_ref.current:
            visible_markers = self.all_markers.get(self.current_layer, [])
            self.marker_layer_ref.current.markers = visible_markers
            print(f"✅ Mostrando {len(visible_markers)} marcadores de {self.current_layer}")
            
            # Debug: mostrar primeros marcadores
            if len(visible_markers) > 0:
                print(f"   🔍 Primer marcador: {visible_markers[0].coordinates}")
            
            if self._page_ref:
                self._page_ref.update()
    
    def on_marker_click(self, marker_data):
        """Maneja el click en un marcador."""
        self.selected_marker_data = marker_data
        self._update_info_card()
    
    def _update_info_card(self):
        """Actualiza la tarjeta de información con los datos del marcador seleccionado."""
        if not self.info_card_ref.current or not self.selected_marker_data:
            return
        
        data = self.selected_marker_data
        
        # Crear contenido según el tipo de dato
        self.info_card_ref.current.visible = True
        self.info_card_ref.current.content = self._create_info_card_content(data)
        
        if self._page_ref:
            self._page_ref.update()
    
    def _close_info_card(self, e):
        """Cierra la tarjeta de información."""
        if self.info_card_ref.current:
            self.info_card_ref.current.visible = False
            self.selected_marker_data = None
            if self._page_ref:
                self._page_ref.update()
    
    def _create_info_card_content(self, data):
        """Crea el contenido de la tarjeta de información."""
        tipo = data.get("tipo", "")
        
        # Header con título y botón cerrar
        header = ft.Row(
            controls=[
                ft.Icon(data.get("icon", ft.icons.Icons.INFO), color=data.get("color", COLORS["primary"]), size=24),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(data.get("titulo", "Información"), size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_white"]),
                        ft.Text(tipo.replace("_", " ").title(), size=10, color=COLORS["text_gray"], italic=True)
                    ],
                    expand=True
                ),
                ft.IconButton(
                    icon=ft.icons.Icons.CLOSE,
                    icon_color=COLORS["text_gray"],
                    icon_size=20,
                    on_click=self._close_info_card
                )
            ]
        )
        
        # Contenido según tipo
        info_items = []
        has_valid_data = False
        
        for key, value in data.get("info", {}).items():
            # Verificar si hay datos reales
            # Para tráfico, cualquier estado válido (0-9) es un dato real
            if tipo == "trafico" and key == "Estado" and value not in ["Sin datos", "Sin información", "Desconocido"]:
                has_valid_data = True
            elif value and str(value) not in ["-", "None", "", "Sin datos"]:
                has_valid_data = True
            
            # Formatear valor
            display_value = str(value) if value and str(value) not in ["None", ""] else "Sin datos"
            
            info_items.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=4),
                    content=ft.Row(
                        controls=[
                            ft.Text(f"{key}:", size=11, color=COLORS["text_gray"], weight=ft.FontWeight.BOLD, width=100),
                            ft.Text(display_value, size=11, color=COLORS["text_white"] if display_value != "Sin datos" else COLORS["text_gray"])
                        ]
                    )
                )
            )
        
        # Mensaje si no hay datos activos
        if not has_valid_data and tipo == "trafico":
            info_items.append(
                ft.Container(
                    padding=10,
                    margin=ft.margin.only(top=10),
                    bgcolor="#ffd70022",
                    border_radius=8,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.icons.Icons.INFO_OUTLINE, color=COLORS["traffic"], size=16),
                            ft.Text(
                                "Sensor sin datos en este momento",
                                size=10,
                                color=COLORS["text_gray"],
                                italic=True,
                                expand=True
                            )
                        ]
                    )
                )
            )
        
        return ft.Column(
            spacing=8,
            controls=[
                header,
                ft.Divider(color=COLORS["panel_medium"], height=1),
                ft.Column(spacing=2, controls=info_items, scroll=ft.ScrollMode.AUTO, height=200 if len(info_items) > 5 else None)
            ]
        )
    
    def _create_content(self):
        """Crea el contenido del mapa."""
        return ft.Stack(
            controls=[
                self._create_map(),
                self._create_layer_selector(),
                self._create_info_card(),
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
                bgcolor="#1a2332ff",
                border_radius=10,
                padding=10,
                content=ft.Column(
                    spacing=8,
                    controls=[
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
    
    def _create_info_card(self):
        """Crea la tarjeta de información para mostrar detalles del marcador."""
        return ft.Container(
            ref=self.info_card_ref,
            right=20,
            top=20,
            width=320,
            visible=False,
            bgcolor=COLORS["panel_dark"],  # Más opaco (f5 = 96% opacidad)
            border_radius=15,
            padding=20,
            border=ft.border.all(2, COLORS["primary"]),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color="#00ff8844",
            ),
            # Gradiente de fondo sutil
            gradient=ft.LinearGradient(
                begin=ft.alignment.Alignment(-1, -1),
                end=ft.alignment.Alignment(1, 1),
                colors=[COLORS["panel_dark"], COLORS["panel_medium"]]
            ),
            content=ft.Text("Cargando...", color=COLORS["text_white"])
        )
    
    def _create_marker(self, lat, lon, color, icon=ft.icons.Icons.LOCATION_ON, marker_data=None):
        """Crea un marcador clickeable con datos asociados."""
        
        def on_icon_click(e):
            if marker_data:
                self.on_marker_click(marker_data)
        
        # Crear color con transparencia para el fondo
        bg_color = color + "33"  # Agregar transparencia (20%)
        
        return mapa.Marker(
            content=ft.GestureDetector(
                on_tap=on_icon_click,
                content=ft.Container(
                    width=35,
                    height=35,
                    bgcolor=bg_color,
                    border_radius=20,
                    alignment=ft.alignment.Alignment(0, 0),  # Centrar el icono
                    content=ft.Icon(
                        icon,
                        color=color,
                        size=22
                    )
                )
            ),
            coordinates=mapa.MapLatitudeLongitude(lat, lon),
        )
    
    def load_markers(self):
        """Carga marcadores de estaciones de sensores en el mapa."""
        try:
            from utils import get_cached_weather_data, get_cached_air_quality_data, get_cached_traffic_data
            from utils.avamet_coordinates import get_station_coordinates
            
            weather_data = get_cached_weather_data()
            air_quality_data = get_cached_air_quality_data()
            traffic_data = get_cached_traffic_data()
            
            # Limpiar marcadores existentes
            for key in self.all_markers:
                self.all_markers[key] = []
            
            # Marcadores de precipitaciones (AVAMET)
            for clima in weather_data:
                if clima.prec and clima.prec != "-":
                    # Obtener coordenadas GPS de la estación
                    coords = get_station_coordinates(clima.estacion)
                    
                    if coords:
                        # Determinar color según precipitación
                        color = COLORS["precipitation"]
                        try:
                            prec_value = float(clima.prec)
                            if prec_value > 10:
                                color = COLORS["event_danger"]
                            elif prec_value > 5:
                                color = COLORS["traffic"]
                        except:
                            pass
                        
                        
                        marker_data = {
                            "tipo": "precipitacion",
                            "titulo": clima.estacion,
                            "icon": ft.icons.Icons.WATER_DROP,
                            "color": color,
                            "info": {
                                "Precipitación": f"{clima.prec} mm",
                                "Temperatura": f"{clima.tmed}°C",
                                "Humedad": f"{clima.hr}%"
                            }
                        }
                        
                        marker = self._create_marker(
                            coords["lat"], coords["lon"], color, ft.icons.Icons.WATER_DROP, marker_data
                        )
                        self.all_markers["Precipitaciones"].append(marker)
            
            # Marcadores de contaminación NO2
            for estacion in air_quality_data:
                if estacion.geo_point_2d and estacion.no2 and estacion.no2 != "-":
                    lat = estacion.geo_point_2d.get("lat")
                    lon = estacion.geo_point_2d.get("lon")
                    
                    if lat and lon:
                        # Determinar color según nivel de NO2
                        color = COLORS["primary"]
                        try:
                            no2_value = float(estacion.no2)
                            if no2_value > 40:
                                color = COLORS["event_danger"]
                            elif no2_value > 20:
                                color = COLORS["traffic"]
                        except:
                            pass
                        
                        
                        marker_data = {
                            "tipo": "no2",
                            "titulo": estacion.direccion,
                            "icon": ft.icons.Icons.CLOUD,
                            "color": color,
                            "info": {
                                "NO2": f"{estacion.no2} μg/m³",
                                "Calidad": estacion.calidad_am,
                                "Estación": estacion.direccion
                            }
                        }
                        
                        marker = self._create_marker(
                            lat, lon, color, ft.icons.Icons.CLOUD, marker_data
                        )
                        self.all_markers["Contaminación (NO2)"].append(marker)
            
            # Marcadores de contaminación O3/PM10
            for estacion in air_quality_data:
                if estacion.geo_point_2d and (estacion.o3 != "-" or estacion.pm10 != "-"):
                    lat = estacion.geo_point_2d.get("lat")
                    lon = estacion.geo_point_2d.get("lon")
                    
                    if lat and lon:
                        
                        marker_data = {
                            "tipo": "o3_pm10",
                            "titulo": estacion.direccion,
                            "icon": ft.icons.Icons.BLUR_ON,
                            "color": COLORS["pollution"],
                            "info": {
                                "O3": f"{estacion.o3} μg/m³",
                                "PM10": f"{estacion.pm10} μg/m³",
                                "Estación": estacion.direccion
                            }
                        }
                        
                        marker = self._create_marker(
                            lat, lon, COLORS["pollution"], ft.icons.Icons.BLUR_ON, marker_data
                        )
                        self.all_markers["Contaminación (O3, PM10)"].append(marker)
            
            # Marcadores de tráfico DGT
            for estacion in traffic_data:
                if estacion.geo_point_2d:
                    lat = estacion.geo_point_2d.get("lat")
                    lon = estacion.geo_point_2d.get("lon")
                    
                    if lat and lon:
                        # Importar función de decodificación de estado
                        from utils.RealTimeTrafficValencia import get_estado_descripcion
                        
                        # Obtener descripción y color sugerido del estado
                        estado_desc, color_sugerido = get_estado_descripcion(estacion.estado)
                        
                        # Determinar color según estado del tráfico
                        color_map = {
                            "green": COLORS["primary"],
                            "yellow": COLORS["traffic"],
                            "red": COLORS["event_danger"],
                            "gray": COLORS["text_gray"]
                        }
                        color = color_map.get(color_sugerido, COLORS["traffic"])
                        
                        
                        # Construir info solo con datos disponibles
                        info = {"Estado": estado_desc, "Código": f"{estacion.estado}"}
                        
                        # Solo agregar campos si tienen datos reales
                        if estacion.velocidad and estacion.velocidad != "-":
                            info["Velocidad"] = f"{estacion.velocidad} km/h"
                        if estacion.intensidad and estacion.intensidad != "-":
                            info["Intensidad"] = f"{estacion.intensidad} veh/h"
                        if estacion.ocupacion and estacion.ocupacion != "-":
                            info["Ocupación"] = f"{estacion.ocupacion}%"
                        
                        marker_data = {
                            "tipo": "trafico",
                            "titulo": estacion.denominacion,
                            "icon": ft.icons.Icons.TRAFFIC,
                            "color": color,
                            "info": info
                        }
                        
                        marker = self._create_marker(
                            lat, lon, color, ft.icons.Icons.TRAFFIC, marker_data
                        )
                        self.all_markers["Flujo Tráfico DGT"].append(marker)
            
            # Actualizar marcadores visibles
            self.update_visible_markers()
            
            total_markers = sum(len(markers) for markers in self.all_markers.values())
            print(f"✅ {total_markers} marcadores cargados en total")
            print(f"   📍 Precipitaciones: {len(self.all_markers['Precipitaciones'])}")
            print(f"   📍 NO2: {len(self.all_markers['Contaminación (NO2)'])}")
            print(f"   📍 O3/PM10: {len(self.all_markers['Contaminación (O3, PM10)'])}")
            print(f"   📍 Tráfico: {len(self.all_markers['Flujo Tráfico DGT'])}")
            
        except Exception as e:
            print(f"❌ Error al cargar marcadores: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_footer(self):
        """Crea el footer con fuente de datos."""
        return ft.Container(
            bottom=20,
            left=20,
            content=ft.Text(
                "Source: AVAMET, GVA OpenData & Valencia Traffic",
                color=COLORS["primary"],
                size=10,
            )
        )
