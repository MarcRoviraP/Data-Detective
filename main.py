import flet as ft
import os
from components import LeftPanel, MapContainer, RightPanel


class DataDetectiveUI(ft.Row):
    """Interfaz principal de Data Detective."""

    def __init__(self, page: ft.Page):
        super().__init__(spacing=0, expand=True)

        # Crear MapContainer primero
        self.map_container = MapContainer(page=page)

        # Crear LeftPanel con callback al MapContainer
        self.left_panel = LeftPanel(
            page=page,
            on_layer_change=self.map_container.on_layer_change
        )

        # Crear RightPanel
        self.right_panel = RightPanel(page=page)

        # Agregar los paneles a la fila
        self.controls = [
            self.left_panel,
            self.map_container,
            self.right_panel,
        ]


def main(page: ft.Page):
    """Función principal de la aplicación."""
    page.title = "Data Detective - VLC Urban Intel"
    page.padding = 0
    page.window.maximized = True
    page.window.icon = "ico/ico.ico"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed="blue"
    )

    # Verificar y generar datos si es necesario
    from utils.data_verifier import verify_and_generate_data

    # Mostrar splash screen mientras se verifica
    splash_progress_text = ft.Text(
        "Verificando...", size=14, color=ft.Colors.BLUE_400)
    splash = ft.Container(
        content=ft.Column([
            ft.Text("Verificando datos históricos...",
                    size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.ProgressBar(width=400, color=ft.Colors.BLUE_400),
            ft.Container(height=10),
            splash_progress_text,
            ft.Container(height=5),
            ft.Text("Esto puede tardar unos minutos en la primera ejecución",
                    size=12, color=ft.Colors.GREY_400)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.Alignment(0, 0),
        expand=True,
        bgcolor="#0a0e1a"
    )
    page.add(splash)
    page.update()

    # Verificar datos (puede mostrar diálogo de generación)
    data_ready = verify_and_generate_data(page)

    # Si los datos están listos, pre-cargar datos de APIs en paralelo
    if data_ready:
        import threading
        import time
        
        # Actualizar mensaje del splash
        splash_progress_text.value = "Cargando datos en tiempo real..."
        page.update()
        
        # Variables para rastrear progreso
        loading_status = {
            "weather": False,
            "air_quality": False,
            "traffic": False
        }
        
        # Pre-cargar datos de APIs en threads paralelos
        def preload_weather():
            from utils import get_cached_weather_data
            get_cached_weather_data()
            loading_status["weather"] = True
            update_progress()
        
        def preload_air_quality():
            from utils import get_cached_air_quality_data
            get_cached_air_quality_data()
            loading_status["air_quality"] = True
            update_progress()
        
        def preload_traffic():
            from utils import get_cached_traffic_data
            get_cached_traffic_data()
            loading_status["traffic"] = True
            update_progress()
        
        def update_progress():
            completed = sum(loading_status.values())
            total = len(loading_status)
            splash_progress_text.value = f"Cargando datos... ({completed}/{total})"
            page.update()
        
        # Iniciar threads paralelos
        weather_thread = threading.Thread(target=preload_weather, daemon=True)
        air_quality_thread = threading.Thread(target=preload_air_quality, daemon=True)
        traffic_thread = threading.Thread(target=preload_traffic, daemon=True)
        
        weather_thread.start()
        air_quality_thread.start()
        traffic_thread.start()
        
        # Esperar a que todos terminen (máximo 15 segundos)
        start_time = time.time()
        while not all(loading_status.values()) and (time.time() - start_time) < 15:
            time.sleep(0.1)
        
        page.clean()  # Limpiar splash screen

        # Agregar la UI principal
        ui = DataDetectiveUI(page)
        page.add(ui)

        # Configurar event handlers después de que la página esté lista
        ui.right_panel.setup_event_handlers()
    else:
        # Si no están listos, el diálogo de generación se encargará
        # Cuando termine, se llamará a esta función de nuevo
        import time
        import threading

        def wait_and_load():
            # Esperar a que termine la generación
            time.sleep(3)
            # Verificar si ya terminó
            data_dir = os.path.join(os.path.dirname(
                __file__), "data", "pollution_historical")
            metadata_path = os.path.join(data_dir, "metadata.json")

            if os.path.exists(metadata_path):
                page.clean()
                ui = DataDetectiveUI(page)
                page.add(ui)
                ui.right_panel.setup_event_handlers()
                page.update()

        thread = threading.Thread(target=wait_and_load, daemon=True)
        thread.start()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
