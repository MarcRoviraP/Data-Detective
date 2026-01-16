import requests
import datetime

class EstacionContaminacionAtmosferica:
    direccion, no2, pm10, o3, fecha_carg, calidad_am = "-", "-", "-", "-", "-", "-"
 
    
    def imprimir_informacion(self):
        print(f"📍 {self.direccion}")
        print(f"🕒 {self.format_timestamp(self.fecha_carg)}")
        print(f"   - NO2 : {self.format_value(self.no2)} µg/m³")
        print(f"   - PM10: {self.format_value(self.pm10)} µg/m³")
        print(f"   - O3  : {self.format_value(self.o3)} µg/m³")
        print(f"   - Calidad: {self.calidad_am}")
        print("-" * 40)

    def format_timestamp(self, fecha) -> str:

        if not fecha:
            return "-"
        
        try:
            dt = datetime.datetime.fromisoformat(fecha)
            return dt.strftime("%d-%m-%Y %H:%M:%S")
        except (ValueError, TypeError):
            return fecha
        
    def format_value(self, value) -> str:
        return str(value) if value is not None else "-"
        
def main():
    URL = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records?select=direccion%2Cno2%2Cpm10%2Co3%2Cfecha_carg%2Ccalidad_am&limit=20"

    response = requests.get(URL, timeout=15)
    json = response.json().get("results", [])

    lista_estaciones = []

    for record in json:
        estacion = EstacionContaminacionAtmosferica()
        estacion.direccion = record.get("direccion", "-")
        estacion.no2 = record.get("no2", "-")
        estacion.pm10 = record.get("pm10", "-")
        estacion.o3 = record.get("o3", "-")
        estacion.fecha_carg = record.get("fecha_carg", "-")
        estacion.calidad_am = record.get("calidad_am", "-")

        lista_estaciones.append(estacion)

    for estacion in lista_estaciones:
        estacion.imprimir_informacion()

if __name__ == "__main__":
    main()