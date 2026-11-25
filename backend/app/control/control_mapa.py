"""CU-13 Visualizar bus en el mapa y CU-14 Consultar datos del vehículo (RN-305 a RN-307)."""
from app.control.control_llegada import ControlLlegada
from app.entidades.novedad import Novedad
from app.entidades.paradero import RutaParadero
from app.entidades.recorrido import Recorrido
from app.entidades.ruta import Ruta
from app.entidades.usuario import Conductor
from app.entidades.vehiculo import Vehiculo
from app.errores import ErrorNegocio

REFRESCO_SEGUNDOS = 10  # RN-305


class ControlMapa:
    @staticmethod
    def consultar_trazado(bd, id_ruta: int) -> dict:
        ruta = Ruta.consultar(bd, id_ruta)
        if ruta is None:
            raise ErrorNegocio(404, "Ruta no encontrada")
        coords = ruta["trazado"]["coordinates"] if ruta["trazado"] else []
        return {"id_ruta": ruta["id_ruta"], "codigo": ruta["codigo"], "nombre": ruta["nombre"], "estado": ruta["estado"],
                "trazado": [[lat, lon] for lon, lat in coords],
                "paraderos": [{**p, "latitud": float(p["latitud"]), "longitud": float(p["longitud"])} for p in RutaParadero.paraderos_de_ruta(bd, id_ruta)],
                "refresco_segundos": REFRESCO_SEGUNDOS}

    @staticmethod
    def consultar_buses(bd, id_ruta: int, id_paradero: int | None) -> dict:
        if Ruta.consultar(bd, id_ruta) is None:
            raise ErrorNegocio(404, "Ruta no encontrada")
        km = None
        if id_paradero:
            rp = RutaParadero.consultar(bd, id_ruta, id_paradero)
            if rp is None:
                raise ErrorNegocio(404, "El paradero no pertenece a la ruta")
            km = rp["km_desde_inicio"]
        buses = ControlLlegada.buses_de_ruta(bd, id_ruta, km)
        resp = {"id_ruta": id_ruta, "buses": buses, "refresco_segundos": REFRESCO_SEGUNDOS}
        if not buses:
            resp["mensaje"] = "No hay buses en camino"
            resp["proxima_salida"] = ControlLlegada.proxima_salida(bd, id_ruta)
        return resp

    @staticmethod
    def consultar_ficha(bd, id_recorrido: int) -> dict:
        r = Recorrido.consultar(bd, id_recorrido)
        if r is None:
            raise ErrorNegocio(404, "Recorrido no encontrado")
        if r["id_estado"] != 1:
            raise ErrorNegocio(410, "Este recorrido ya terminó")
        v = Vehiculo.consultar(bd, r["id_vehiculo"])
        c = Conductor.consultar_publico(bd, r["id_usuario"])  # RN-307: solo nombre y foto
        nov = Novedad.ultima_de_recorrido(bd, id_recorrido)
        return {"id_recorrido": id_recorrido, "numero_interno": v["numero_interno"], "placa": f"{v['placa'][:3]} {v['placa'][3:]}", "tipo": v["tipo"],
                "empresa": v["empresa"], "conductor": {"nombre": c["nombre"], "foto_url": c["foto_url"]},
                "hora_salida": f"{r['fecha_inicio']:%H:%M}", "ruta": {"codigo": r["ruta_codigo"], "nombre": r["ruta_nombre"]},
                "estado": "En curso" + (f" — {nov['tipo']}: {nov['comentario']}" if nov else " — sin novedades")}
