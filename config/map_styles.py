"""
Configuración de estilos de mapas disponibles.
"""

MAP_STYLES = {
    "Normal": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "Satélite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "Oscuro": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    "Topográfico": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    
}
