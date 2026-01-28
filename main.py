import flet as ft
from components import LeftPanel, MapContainer, RightPanel


class DataDetectiveUI(ft.Row):
    """Interfaz principal de Data Detective."""
    
    def __init__(self):
        super().__init__(spacing=0, expand=True)
        
        # Crear los tres paneles principales
        self.left_panel = LeftPanel()
        self.map_container = MapContainer()
        self.right_panel = RightPanel()
        
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
    page.add(DataDetectiveUI())


if __name__ == "__main__":
    ft.run(main)
