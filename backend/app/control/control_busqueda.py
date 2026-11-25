"""CU-12 Buscar rutas por destino (RN-301 a RN-304)."""
import unicodedata

from app.control.control_llegada import ControlLlegada
from app.entidades.paradero import Paradero, RutaParadero
from app.errores import ErrorNegocio

MIN_LETRAS = 3


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y sin espacios repetidos (RN-301)."""
    t = unicodedata.normalize("NFD", texto.strip().lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(t.split())


def letras_efectivas(texto: str) -> int:
    return sum(1 for c in texto if c.isalpha())


class ControlBusqueda:
    @staticmethod
    def buscar_rutas(bd, texto: str, lat: float, lon: float) -> dict:
        if letras_efectivas(texto or "") < MIN_LETRAS:
            raise ErrorNegocio(400, "Escribe al menos 3 letras")
        destinos = Paradero.buscar_por_nombre(bd, normalizar(texto))
        resultados = []
        if destinos:
            for r in RutaParadero.rutas_hacia(bd, [d["id_paradero"] for d in destinos], lat, lon):
                buses = ControlLlegada.buses_de_ruta(bd, r["id_ruta"], r["km_abordaje"])
                en_camino = sorted((b for b in buses if b["eta"]["estado"] != "YA_PASO"), key=lambda b: b["eta"]["minutos"] or 0)
                prox = en_camino[0] if en_camino else None
                resultados.append({
                    "id_ruta": r["id_ruta"], "codigo": r["codigo"], "nombre": r["nombre"],
                    "sentido": f"{r['origen']} → {r['destino']}",
                    "abordaje": {"id_paradero": r["id_abordaje"], "nombre": r["abordaje"], "metros": int(r["metros_abordaje"])},
                    "destino": {"id_paradero": r["id_destino"], "nombre": r["destino_paradero"]},
                    "vehiculos_operando": len(buses),
                    "proximo_bus": prox and {"numero_interno": prox["numero_interno"], "eta": prox["eta"],
                                             "indicador": f"Bus {prox['numero_interno']} " + ("llegando" if prox["eta"]["estado"] == "LLEGANDO" else f"llega en {prox['eta']['texto']}")},
                    "proxima_salida": None if prox else ControlLlegada.proxima_salida(bd, r["id_ruta"]),
                })
        # RN-304: primero las rutas con bus en camino, por el que llega antes
        resultados.sort(key=lambda x: (x["proximo_bus"] is None, x["proximo_bus"]["eta"]["minutos"] if x["proximo_bus"] else 0, x["codigo"]))
        resp = {"texto": texto.strip(), "resultados": resultados}
        if not resultados:
            resp["mensaje"] = f"No encontramos rutas hacia {texto.strip()}"
        return resp
