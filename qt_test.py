import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)

# Crear el widget de navegador
view = QWebEngineView()

# Cargar una web
view.setHtml("""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prueba de Qt WebEngine</title>
</head>
<body>
    <iframe src="https://valencia.opendatasoft.com/explore/embed/dataset/estacions-atmosferiques-estaciones-atmosfericas/map/?location=12,39.44838,-0.33663&basemap=e4bf90&static=false&datasetcard=false&scrollWheelZoom=false" width="400" height="300" frameborder="0"></iframe>
</body>
</html>""")

# Mostrar
view.resize(1024, 768)
view.show()

sys.exit(app.exec())
