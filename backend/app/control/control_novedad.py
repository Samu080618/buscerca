"""CU-205 Reportar novedad."""
from app import reloj
from app.entidades.novedad import Novedad, TipoNovedad
from app.entidades.recorrido import Recorrido
from app.errores import ErrorNegocio

MAX_COMENTARIO = 200


class ControlNovedad:
    @staticmethod
    def listar_tipos(bd):
        return TipoNovedad.listar(bd)

    @staticmethod
    def registrar_novedad(bd, usuario, id_recorrido, id_tipo, comentario, latitud, longitud) -> dict:
        r = Recorrido.consultar(bd, id_recorrido)
        if r is None or r["id_usuario"] != usuario["id"] or r["id_estado"] != 1:
            raise ErrorNegocio(409, "No hay recorrido en curso")
        if not id_tipo or not TipoNovedad.existe(bd, id_tipo):
            raise ErrorNegocio(400, "Selecciona el tipo de novedad")
        if comentario and len(comentario) > MAX_COMENTARIO:
            raise ErrorNegocio(400, "El comentario admite máximo 200 caracteres")
        fecha = reloj.ahora()
        id_n = Novedad.guardar(bd, id_recorrido, id_tipo, (comentario or "").strip() or None, latitud, longitud, fecha)
        return {"id_novedad": id_n, "mensaje": "Novedad reportada", "fecha_hora": fecha}
