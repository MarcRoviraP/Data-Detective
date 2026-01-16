import requests
from bs4 import BeautifulSoup

class Clima:
    def __init__(self):
        self.estacion = ""
        self.tmin   = ""
        self.tmed   = ""
        self.tmax   = ""
        self.hr     = ""
        self.prec   = ""
        self.vmed   = ""
        self.vdir   = ""
        self.vmax   = ""

def main():
    url = "https://www.avamet.org/mx-meteoxarxa.php?territori=c15"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    tabla = soup.find("table", class_="tDades")
    if not tabla:
        raise RuntimeError("No se encontró la tabla con clase 'tDades'")

    filas = tabla.select("tr")
    datos = []

    for tr in filas:
        celdas = tr.find_all("td")
        if len(celdas) != 9:          # saltar cabeceras o filas sin datos
            continue

        c = Clima()
        c.estacion = celdas[0].get_text(" ", strip=True)   # nombre + barrio
        c.tmin     = celdas[1].get_text(strip=True)
        c.tmed     = celdas[2].get_text(strip=True)
        c.tmax     = celdas[3].get_text(strip=True)
        c.hr       = celdas[4].get_text(strip=True)
        c.prec     = celdas[5].get_text(strip=True)
        c.vmed     = celdas[6].get_text(strip=True)
        c.vdir     = celdas[7].get_text(strip=True)
        c.vmax     = celdas[8].get_text(strip=True)
        datos.append(c)


    for d in datos:
        print(f"{d.estacion:60} Tmin: {d.tmin:>5} Tmed: {d.tmed:>5} Tmax: {d.tmax:>5} HR: {d.hr:>5} Prec: {d.prec:>5} Vmed: {d.vmed:>5} Vdir: {d.vdir:>5} Vmax: {d.vmax:>5}")
        
        
if __name__ == "__main__":
    main()