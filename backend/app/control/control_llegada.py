"""CU-15 Consultar tiempo de llegada al paradero y CU-15.1 Calcular tiempo estimado de llegada (ETA)."""
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from app import reloj
from app.entidades.paradero import Paradero, RutaParadero
from app.entidades.recorrido import Recorrido
from app.entidades.ruta import Ruta
from app.entidades.ubicacion import Ubicacion
from app.errores import ErrorNegocio

VEL_MINIMA = Decimal("5")            # RN-308: por debajo se usa la velocidad histórica
UMBRAL_LLEGANDO = Decimal("2")       # menos de 2 minutos → "Llegando"
SENAL_GRIS = timedelta(minutes=2)    # RN-306
SENAL_OCULTA = timedelta(minutes=15)  # RN-306


def clasificar_senal(fecha_ultima, ahora) -> str:
    """RN-306: ACTIVA (< 2 min), SIN_SENAL (2 a < 15 min) u OCULTA (15 min o más)."""
    edad = ahora - fecha_ultima
    if edad < SENAL_GRIS:
        return "ACTIVA"
    return "SIN_SENAL" if edad < SENAL_OCULTA else "OCULTA"


class ControlLlegada:
    @staticmethod
    def calcular_eta(km_bus, km_paradero, velocidad_promedio, velocidad_historica) -> dict:
        """CU-15.1 (RN-308 y RN-309). Devuelve estado, minutos y el texto que ve el pasajero."""
        km_bus, km_paradero = Decimal(str(km_bus)), Decimal(str(km_paradero))
        if km_bus > km_paradero:
            return {"estado": "YA_PASO", "minutos": None, "aproximado": False, "texto": "Ya pasó"}
        vel = Decimal(str(velocidad_promedio)) if velocidad_promedio is not None else None
        aproximado = vel is None or vel < VEL_MINIMA
        if aproximado:
            vel = Decimal(str(velocidad_historica))
        minutos = (km_paradero - km_bus) / vel * 60
        if minutos < UMBRAL_LLEGANDO:
            return {"estado": "LLEGANDO", "minutos": float(round(minutos, 1)), "aproximado": aproximado, "texto": "Llegando"}
        entero = int(minutos.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return {"estado": "EN_CAMINO", "minutos": entero, "aproximado": aproximado,
                "texto": f"{entero} min" + (" aprox." if aproximado else "")}

    @staticmethod
    def buses_de_ruta(bd, id_ruta: int, km_paradero=None) -> list[dict]:
        """Buses EN CURSO de la ruta con su última posición, señal y (si hay paradero) ETA."""
        ruta = Ruta.consultar(bd, id_ruta)
        ahora = reloj.ahora()
        buses = []
        for r in Recorrido.en_curso_de_ruta(bd, id_ruta):
            u = Ubicacion.ultima(bd, r["id_recorrido"])
            if u is None:
                continue
            senal = clasificar_senal(u["fecha_hora"], ahora)
            if senal == "OCULTA":
                continue
            bus = {"id_recorrido": r["id_recorrido"], "numero_interno": r["numero_interno"], "placa": r["placa"],
                   "latitud": float(u["latitud"]), "longitud": float(u["longitud"]), "km_en_ruta": u["km_en_ruta"],
                   "velocidad_promedio": u["velocidad_promedio"], "senal": senal, "ultima_senal": u["fecha_hora"],
                   "etiqueta": None if senal == "ACTIVA" else f"Sin señal desde {u['fecha_hora']:%H:%M}"}
            if km_paradero is not None and u["km_en_ruta"] is not None:
                bus["eta"] = ControlLlegada.calcular_eta(u["km_en_ruta"], km_paradero, u["velocidad_promedio"], ruta["velocidad_historica_kmh"])
            buses.append(bus)
        return buses

    @staticmethod
    def proxima_salida(bd, id_ruta: int) -> str | None:
        p = Recorrido.proxima_salida(bd, id_ruta, reloj.ahora())
        return p and f"{p['fecha_inicio']:%H:%M}"

    @staticmethod
    def consultar_llegadas(bd, id_paradero: int, id_ruta: int) -> dict:
        paradero = Paradero.consultar(bd, id_paradero)
        if paradero is None:
            raise ErrorNegocio(404, "Paradero no encontrado")
        rp = RutaParadero.consultar(bd, id_ruta, id_paradero)
        if rp is None:
            raise ErrorNegocio(400, "El paradero no pertenece a la ruta")
        buses = ControlLlegada.buses_de_ruta(bd, id_ruta, rp["km_desde_inicio"])
        orden = {"LLEGANDO": 0, "EN_CAMINO": 1, "YA_PASO": 2}
        buses.sort(key=lambda b: (orden[b["eta"]["estado"]], b["eta"]["minutos"] or 0))
        en_camino = [b for b in buses if b["eta"]["estado"] != "YA_PASO"]
        resp = {"paradero": paradero, "ruta": id_ruta, "llegadas": buses}
        if not en_camino:
            salida = ControlLlegada.proxima_salida(bd, id_ruta)
            resp["mensaje"] = "No hay buses en camino"
            resp["proxima_salida"] = salida
        return resp
