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
    data_dir = os.path.join(os.path.dirname(__file__),
                            "data", "pollution_historical")
    metadata_path = os.path.join(data_dir, "metadata.json")
    csv_path = os.path.join(os.path.dirname(__file__),
                            "valencia_pollution_consolidated.csv")

    # Verificar si ya existen los datos JSON
    if os.path.exists(metadata_path):
        print("✅ Datos históricos JSON ya disponibles")
        return True

    # Verificar si existe el CSV fuente
    if not os.path.exists(csv_path):
        show_error_dialog(page,
                          "❌ CSV No Encontrado",
                          f"No se encontró el archivo:\n{csv_path}\n\n"
                          "Por favor, asegúrate de tener valencia_pollution_consolidated.csv "
                          "en el directorio raíz del proyecto."
                          )
        return False

    # Mostrar diálogo de generación
    print("⚠️ Datos JSON no encontrados. Generando automáticamente...")
    show_generation_dialog(page, csv_path, data_dir)
    return False  # Retornar False para que la app espere


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
                dialog.open = False
                page.update()

                # Mostrar mensaje de éxito y reiniciar app
                success_dialog = ft.AlertDialog(
                    title=ft.Text("✅ Datos Generados", color=ft.colors.GREEN),
                    content=ft.Text(
                        f"Archivos JSON creados exitosamente en:\n{
                            data_dir}\n\n"
                        "La aplicación se cargará ahora con los datos optimizados."
                    ),
                    actions=[
                        ft.TextButton("Continuar", on_click=lambda e: close_and_reload(
                            page, success_dialog))
                    ]
                )
                page.dialog = success_dialog
                success_dialog.open = True
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
