"""Entidad Usuario (Módulo 01). El Conductor es un usuario con rol CONDUCTOR."""
import bcrypt


class Usuario:
    @staticmethod
    def buscar_por_correo(bd, correo: str):
        return bd.consultar_uno("SELECT * FROM usuario WHERE lower(correo) = lower(%s) AND activo", (correo,))

    @staticmethod
    def buscar(bd, id_usuario: int):
        return bd.consultar_uno("SELECT * FROM usuario WHERE id_usuario = %s", (id_usuario,))

    @staticmethod
    def crear(bd, nombre, correo, contrasena, rol, documento=None, telefono=None, direccion=None, foto_url=None) -> int:
        h = bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt(rounds=8)).decode()
        fila = bd.consultar_uno(
            """INSERT INTO usuario (nombre, correo, contrasena_hash, rol, documento, telefono, direccion, foto_url)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_usuario""",
            (nombre, correo, h, rol, documento, telefono, direccion, foto_url))
        return fila["id_usuario"]

    @staticmethod
    def verificar_contrasena(usuario: dict, contrasena: str) -> bool:
        return bcrypt.checkpw(contrasena.encode(), usuario["contrasena_hash"].encode())


class Conductor:
    """Datos públicos del conductor (RN-307): solo nombre y foto."""

    @staticmethod
    def consultar_publico(bd, id_usuario: int):
        return bd.consultar_uno("SELECT nombre, foto_url FROM usuario WHERE id_usuario = %s", (id_usuario,))
