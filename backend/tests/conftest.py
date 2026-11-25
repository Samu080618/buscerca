"""Configuración común de las pruebas: base de datos de prueba limpia y reloj fijo en cada caso."""
import os
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "postgresql://buscerca:buscerca@localhost:5432/buscerca_test")

import pytest
from fastapi.testclient import TestClient

from app import reloj
from app.datos.conexion_bd import ConexionBD
from app.main import app
import seed


@pytest.fixture
def bd():
    con = ConexionBD()
    yield con
    con.deshacer()
    con.cerrar()


@pytest.fixture
def datos(bd, request):
    """Siembra la base de prueba con los datos iniciales y fija el reloj del caso."""
    momento = getattr(request.module, "RELOJ", datetime(2026, 11, 19, 7, 0, 0))
    reloj.fijar(momento)
    ids = seed.sembrar(bd, momento)
    bd.confirmar()
    yield ids
    reloj.fijar(None)


@pytest.fixture
def api():
    return TestClient(app)


@pytest.fixture
def sesion(api):
    def _login(correo: str) -> dict:
        r = api.post("/api/auth/login", json={"correo": correo, "contrasena": seed.CLAVE})
        assert r.status_code == 200, r.text
        return {"Authorization": "Bearer " + r.json()["token"]}
    return _login
