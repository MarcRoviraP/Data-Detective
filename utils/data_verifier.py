"""
Verificador y generador automático de datos históricos JSON.
Se ejecuta al iniciar la aplicación para asegurar que los datos estén disponibles.
"""

import os
import sys
import flet as ft


def verify_and_generate_data(page: ft.Page):
    """
    Verifica si existen los archivos JSON históricos.
    Si no existen, ejecuta el generador automáticamente con barra de progreso.
    """
    # Obtener el directorio raíz del proyecto (parent de utils)
    project_root = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(project_root, "data", "pollution_historical")
    metadata_path = os.path.join(data_dir, "metadata.json")
    csv_path = os.path.join(
        project_root, "valencia_pollution_consolidated.csv")

    # Verificar si ya existen los datos JSON
    if os.path.exists(metadata_path):
        print("✅ Datos históricos JSON ya disponibles")
        return True

    # Verificar si existe el CSV fuente
    if not os.path.exists(csv_path):
        print("⚠️ CSV no encontrado. Iniciando descarga automática...")
        show_download_dialog(page, csv_path, data_dir)
        return False

    # Mostrar diálogo de generación JSON
    print("⚠️ Datos JSON no encontrados. Generando automáticamente...")
    show_generation_dialog(page, csv_path, data_dir)
    return False  # Retornar False para que la app espere


def show_download_dialog(page: ft.Page, csv_path: str, data_dir: str):
    """Muestra diálogo con barra de progreso y contador durante la descarga."""

    progress_bar = ft.ProgressBar(width=400, value=0)
    progress_text = ft.Text("0/380", size=16, weight=ft.FontWeight.BOLD)
    status_text = ft.Text("Iniciando descarga de datos históricos...", size=14)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Descargando Datos Históricos",
                      weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([
                ft.Text(
                    "Primera ejecución detectada.\n"
                    "Descargando y convirtiendo datos históricos...\n"
                    "Este proceso puede tardar varios minutos.",
                    size=12
                ),
                ft.Container(height=10),
                progress_bar,
                ft.Container(height=5),
                progress_text,
                ft.Container(height=5),
                status_text,
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.START),
            width=500,
            padding=20
        ),
    )

    page.dialog = dialog
    dialog.open = True
    page.update()

    # Ejecutar descarga en segundo plano
    import threading

    def run_download():
        try:
            # Importar el descargador optimizado
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from utils.optimized_data_downloader import download_and_convert_to_json

            # Callback para actualizar progreso
            def update_progress(current, total, message):
                progress_bar.value = current / total
                progress_text.value = f"{current}/{total}"
                status_text.value = message
                page.update()

            # Ejecutar descarga y conversión directa a JSON
            success = download_and_convert_to_json(
                progress_callback=update_progress)

            if success:
                status_text.value = "✅ Descarga y conversión completadas!"
                progress_bar.value = 1.0
                page.update()

                # Esperar un momento para que el usuario vea el mensaje
                import time
                time.sleep(1)

                # Cerrar diálogo
                dialog.open = False
                page.update()

                # Cargar la UI principal automáticamente
                page.clean()
                from main import DataDetectiveUI
                ui = DataDetectiveUI(page)
                page.add(ui)
                ui.right_panel.setup_event_handlers()
                page.update()
            else:
                status_text.value = "❌ Error durante la descarga"
                progress_bar.value = 0
                page.update()
                show_error_dialog(
                    page, "Error", "No se pudieron descargar los archivos históricos.")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            show_error_dialog(page, "Error Fatal",
                              f"Error durante la descarga:\n{str(e)}")

    thread = threading.Thread(target=run_download, daemon=True)
    thread.start()


def show_generation_dialog(page: ft.Page, csv_path: str, data_dir: str):
    """Muestra diálogo con barra de progreso durante la generación."""

    progress_bar = ft.ProgressBar(width=400, visible=False)
    status_text = ft.Text("Iniciando conversión...", size=14)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Generando Datos Históricos", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([
                ft.Text(
                    "Primera ejecución detectada.\n"
                    "Convirtiendo datos CSV a formato JSON optimizado...",
                    size=12
                ),
                ft.Container(height=10),
                progress_bar,
                ft.Container(height=5),
                status_text,
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.START),
            width=500,
            padding=20
        ),
    )

    page.dialog = dialog
    dialog.open = True
    page.update()

    # Ejecutar conversión en segundo plano
    import threading

    def run_conversion():
        try:
            progress_bar.visible = True
            page.update()

            # Importar y ejecutar el generador
            sys.path.insert(0, os.path.dirname(__file__))
            from utils.generate_json_indexed import csv_to_json_fragmented

            # Callback para actualizar progreso
            def update_progress(message, value=None):
                status_text.value = message
                if value is not None:
                    progress_bar.value = value
                else:
                    progress_bar.value = None  # Indeterminado
                page.update()

            update_progress("📂 Leyendo archivo CSV...", 0.1)
            success = csv_to_json_fragmented()

            if success:
                update_progress("✅ Conversión completada!", 1.0)

                # Esperar un momento para que el usuario vea el mensaje
                import time
                time.sleep(1)

                # Cerrar diálogo
                dialog.open = False
                page.update()

                # Cargar la UI principal automáticamente
                page.clean()
                from main import DataDetectiveUI
                ui = DataDetectiveUI(page)
                page.add(ui)
                ui.right_panel.setup_event_handlers()
                page.update()
            else:
                update_progress("❌ Error durante la conversión", 0)
                show_error_dialog(
                    page, "Error", "No se pudo completar la conversión. Revisa la consola para más detalles.")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            show_error_dialog(page, "Error Fatal",
                              f"Error durante la generación:\n{str(e)}")

    thread = threading.Thread(target=run_conversion, daemon=True)
    thread.start()


def close_and_reload(page: ft.Page, dialog: ft.AlertDialog):
    """Cierra el diálogo y recarga la página."""
    dialog.open = False
    page.update()
    # La app continuará normalmente después de esto


def show_error_dialog(page: ft.Page, title: str, message: str):
    """Muestra un diálogo de error."""
    error_dialog = ft.AlertDialog(
        title=ft.Text(title, color=ft.Colors.RED),
        content=ft.Text(message),
        actions=[
            ft.TextButton("Cerrar", on_click=lambda e: sys.exit(1))
        ]
    )
    page.dialog = error_dialog
    error_dialog.open = True
    page.update()
