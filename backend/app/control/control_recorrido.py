"""CU-201 Iniciar recorrido, CU-206 Finalizar recorrido y CU-207 Consultar estado del recorrido."""
from app import reloj
from app.entidades.recorrido import Recorrido
from app.entidades.ruta import Ruta
from app.entidades.ubicacion import Ubicacion
from app.entidades.vehiculo import Vehiculo
from app.errores import ErrorNegocio


def _publico(r: dict) -> dict:
    return {"id_recorrido": r["id_recorrido"], "estado": r["estado"], "ruta": {"id": r["id_ruta"], "codigo": r["ruta_codigo"], "nombre": r["ruta_nombre"]},
            "vehiculo": {"id": r["id_vehiculo"], "placa": r["placa"], "numero_interno": r["numero_interno"]},
            "fecha_inicio": r["fecha_inicio"], "fecha_fin": r["fecha_fin"]}


class ControlRecorrido:
    @staticmethod
    def consultar_opciones(bd) -> dict:
        return {"rutas": Ruta.listar_activas(bd), "vehiculos": Vehiculo.listar_disponibles(bd)}

    @staticmethod
    def iniciar_recorrido(bd, usuario: dict, id_ruta: int | None, id_vehiculo: int | None) -> dict:
        if not id_ruta or not id_vehiculo:
            raise ErrorNegocio(400, "Selecciona la ruta y el vehículo")
        activo = Recorrido.consultar_activo(bd, usuario["id"])
        if activo:  # RN-201
            raise ErrorNegocio(409, {"mensaje": "Ya tienes un recorrido en curso", "recorrido": _publico(activo)})
        ruta = Ruta.consultar(bd, id_ruta)
        if ruta is None or ruta["estado"] != "Activa":
            raise ErrorNegocio(400, "La ruta no está disponible")
        if not any(v["id_vehiculo"] == id_vehiculo for v in Vehiculo.listar_disponibles(bd)):
            raise ErrorNegocio(409, "El vehículo no está disponible")
        id_rec = Recorrido.crear(bd, usuario["id"], id_ruta, id_vehiculo, reloj.ahora())
        return _publico(Recorrido.consultar(bd, id_rec))

    @staticmethod
    def consultar_estado(bd, usuario: dict) -> dict:
        r = Recorrido.consultar_activo(bd, usuario["id"])
        if r is None:
            raise ErrorNegocio(404, "No hay recorrido en curso")
        ult = Ubicacion.ultima(bd, r["id_recorrido"])
        return {**_publico(r), "velocidad_promedio": ult and ult["velocidad_promedio"], "ultima_ubicacion": ult and ult["fecha_hora"]}

    @staticmethod
    def finalizar_recorrido(bd, usuario: dict, id_recorrido: int) -> dict:
        r = Recorrido.consultar(bd, id_recorrido)
        if r is None or r["id_usuario"] != usuario["id"]:
            raise ErrorNegocio(404, "Recorrido no encontrado")
        if r["id_estado"] != 1:
            raise ErrorNegocio(409, "El recorrido no está en curso")
        Recorrido.finalizar(bd, id_recorrido, reloj.ahora())  # RN-205
        fin = Recorrido.consultar(bd, id_recorrido)
        total = len(Ubicacion.listar(bd, id_recorrido))
        return {**_publico(fin), "ubicaciones_registradas": total,
                "duracion_minutos": round((fin["fecha_fin"] - fin["fecha_inicio"]).total_seconds() / 60)}
