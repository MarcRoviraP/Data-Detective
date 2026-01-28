import flet as ft
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
    page.bgcolor = "#0a0e1a"

    # Agregar la UI principal
    ui = DataDetectiveUI(page)
    page.add(ui)

    # Configurar event handlers después de que la página esté lista
    ui.right_panel.setup_event_handlers()


if __name__ == "__main__":
    ft.run(main)
