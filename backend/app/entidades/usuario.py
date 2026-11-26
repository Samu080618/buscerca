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


class Perfil:
    """Datos que el propio usuario ve y edita (HU-0104)."""

    @staticmethod
    def consultar(bd, id_usuario: int):
        return bd.consultar_uno(
            "SELECT id_usuario, nombre, correo, rol, documento, telefono, direccion, foto_url FROM usuario WHERE id_usuario = %s",
            (id_usuario,))

    @staticmethod
    def actualizar(bd, id_usuario: int, nombre, telefono, direccion):
        bd.ejecutar("UPDATE usuario SET nombre = %s, telefono = %s, direccion = %s WHERE id_usuario = %s",
                    (nombre, telefono, direccion, id_usuario))

    @staticmethod
    def cambiar_contrasena(bd, id_usuario: int, nueva: str):
        h = bcrypt.hashpw(nueva.encode(), bcrypt.gensalt(rounds=8)).decode()
        bd.ejecutar("UPDATE usuario SET contrasena_hash = %s WHERE id_usuario = %s", (h, id_usuario))


class RecuperacionContrasena:
    @staticmethod
    def crear(bd, id_usuario: int, codigo: str, expira):
        bd.ejecutar("UPDATE recuperacion_contrasena SET usado = TRUE WHERE id_usuario = %s AND NOT usado", (id_usuario,))
        h = bcrypt.hashpw(codigo.encode(), bcrypt.gensalt(rounds=6)).decode()
        bd.ejecutar("INSERT INTO recuperacion_contrasena (id_usuario, codigo_hash, expira) VALUES (%s, %s, %s)", (id_usuario, h, expira))

    @staticmethod
    def vigente(bd, id_usuario: int, ahora):
        return bd.consultar_uno(
            """SELECT * FROM recuperacion_contrasena WHERE id_usuario = %s AND NOT usado AND expira > %s
               ORDER BY id_recuperacion DESC LIMIT 1""", (id_usuario, ahora))

    @staticmethod
    def sumar_intento(bd, id_recuperacion: int):
        bd.ejecutar("UPDATE recuperacion_contrasena SET intentos = intentos + 1 WHERE id_recuperacion = %s", (id_recuperacion,))

    @staticmethod
    def marcar_usado(bd, id_recuperacion: int):
        bd.ejecutar("UPDATE recuperacion_contrasena SET usado = TRUE WHERE id_recuperacion = %s", (id_recuperacion,))


class TokenRevocado:
    @staticmethod
    def revocar(bd, jti: str, expira):
        bd.ejecutar("INSERT INTO token_revocado (jti, expira) VALUES (%s, %s) ON CONFLICT DO NOTHING", (jti, expira))

    @staticmethod
    def esta_revocado(bd, jti: str) -> bool:
        return bd.consultar_uno("SELECT 1 FROM token_revocado WHERE jti = %s", (jti,)) is not None
