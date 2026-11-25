"""Capa de acceso a datos: única clase que habla con PostgreSQL (ConexionBD del modelo lógico)."""
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app import config


class ConexionBD:
    def __init__(self, url: str | None = None):
        self.url = url or config.DATABASE_URL
        self._con: psycopg.Connection | None = None

    def abrir(self):
        if self._con is None or self._con.closed:
            self._con = psycopg.connect(self.url, row_factory=dict_row, autocommit=False)
        return self._con

    def consultar(self, sql: str, params: tuple | dict = ()) -> list[dict]:
        with self.abrir().cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() if cur.description else []

    def consultar_uno(self, sql: str, params: tuple | dict = ()) -> dict | None:
        filas = self.consultar(sql, params)
        return filas[0] if filas else None

    def ejecutar(self, sql: str, params: tuple | dict = ()) -> int:
        with self.abrir().cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount

    def confirmar(self):
        if self._con is not None:
            self._con.commit()

    def deshacer(self):
        if self._con is not None and not self._con.closed:
            self._con.rollback()

    def cerrar(self):
        if self._con is not None:
            self._con.close()
            self._con = None

    @contextmanager
    def transaccion(self):
        try:
            yield self
            self.confirmar()
        except Exception:
            self.deshacer()
            raise


def obtener_bd():
    """Dependencia de FastAPI: una conexión por petición."""
    bd = ConexionBD()
    try:
        yield bd
        bd.confirmar()
    except Exception:
        bd.deshacer()
        raise
    finally:
        bd.cerrar()
