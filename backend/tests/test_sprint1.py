"""Casos de prueba del Sprint 1 — Módulo 01: Autenticación y Perfiles (HU-0101 a HU-0105)."""
from datetime import datetime, timedelta

import pytest

import seed
from app import reloj

RELOJ = datetime(2026, 10, 22, 8, 0, 0)
NUEVA = {"nombre": "Camila Suárez", "correo": "camila.suarez@correo.co", "contrasena": "Vereda2026", "rol": "PASAJERO", "telefono": "3109998877"}


def login(api, correo, clave):
    return api.post("/api/auth/login", json={"correo": correo, "contrasena": clave})


@pytest.fixture
def demo_codigo(monkeypatch):
    monkeypatch.setenv("DEMO_CODIGO", "1")


# ---------------- HU-0101 Registro de usuario ----------------
def test_CP_0101_01_registra_pasajero_y_puede_ingresar(api, datos):
    r = api.post("/api/auth/registro", json=NUEVA)
    assert r.status_code == 201 and r.json()["rol"] == "PASAJERO"
    assert login(api, "Camila.Suarez@correo.co", "Vereda2026").json()["usuario"]["nombre"] == "Camila Suárez"


def test_CP_0101_02_correo_repetido(api, datos):
    api.post("/api/auth/registro", json=NUEVA)
    r = api.post("/api/auth/registro", json={**NUEVA, "correo": "CAMILA.SUAREZ@correo.co"})
    assert r.status_code == 409 and r.json()["detail"] == "El correo ya está registrado"


def test_CP_0101_03_valida_correo_contrasena_y_nombre(api, datos, bd):
    for cambio in [{"contrasena": "abc123"}, {"contrasena": "solamenteletras"}, {"correo": "camila@"}, {"nombre": "Ca"}]:
        assert api.post("/api/auth/registro", json={**NUEVA, **cambio}).status_code == 400
    assert bd.consultar_uno("SELECT count(*) AS n FROM usuario WHERE correo = %s", (NUEVA["correo"],))["n"] == 0


def test_CP_0101_04_registro_por_rol(api, datos, sesion):
    assert api.post("/api/auth/registro", json={**NUEVA, "rol": "CONDUCTOR"}).json()["rol"] == "CONDUCTOR"
    admin = {**NUEVA, "correo": "nuevo.admin@buscerca.co", "rol": "ADMINISTRADOR"}
    assert api.post("/api/auth/registro", json=admin).status_code == 403
    assert api.post("/api/auth/registro", json=admin, headers=sesion("admin@buscerca.co")).status_code == 201


# ---------------- HU-0102 Inicio de sesión ----------------
def test_CP_0102_01_ingresa_con_su_rol(api, datos):
    r = login(api, "jorge.ramirez@buscerca.co", seed.CLAVE).json()
    assert r["usuario"]["rol"] == "CONDUCTOR" and r["token"]
    assert api.get("/api/auth/yo", headers={"Authorization": "Bearer " + r["token"]}).json()["nombre"] == "Jorge Ramírez"


def test_CP_0102_02_credenciales_incorrectas(api, datos):
    a, b = login(api, "jorge.ramirez@buscerca.co", "Otra2026"), login(api, "noexiste@buscerca.co", seed.CLAVE)
    assert a.status_code == b.status_code == 401
    assert a.json()["detail"] == b.json()["detail"] == "Correo o contraseña incorrectos"


def test_CP_0102_03_acceso_segun_rol(api, datos, sesion):
    assert api.get("/api/perfil").status_code == 401
    assert api.get("/api/recorridos/opciones", headers=sesion("pasajera@buscerca.co")).status_code == 403
    assert api.get("/api/favoritos", headers=sesion("jorge.ramirez@buscerca.co")).status_code == 403


# ---------------- HU-0103 Recuperación de contraseña ----------------
def test_CP_0103_01_recupera_con_codigo(api, datos, demo_codigo):
    r = api.post("/api/auth/recuperar", json={"correo": "pasajera@buscerca.co"}).json()
    assert len(r["codigo_demo"]) == 6
    ok = api.post("/api/auth/restablecer", json={"correo": "pasajera@buscerca.co", "codigo": r["codigo_demo"], "nueva": "NuevaClave77"})
    assert ok.status_code == 200
    assert login(api, "pasajera@buscerca.co", "NuevaClave77").status_code == 200
    assert login(api, "pasajera@buscerca.co", seed.CLAVE).status_code == 401


def test_CP_0103_02_no_revela_si_el_correo_existe(api, datos, demo_codigo):
    a = api.post("/api/auth/recuperar", json={"correo": "pasajera@buscerca.co"}).json()
    b = api.post("/api/auth/recuperar", json={"correo": "nadie@buscerca.co"}).json()
    assert a["mensaje"] == b["mensaje"] and "codigo_demo" not in b


def test_CP_0103_03_codigo_errado_vencido_o_usado(api, datos, demo_codigo):
    cod = api.post("/api/auth/recuperar", json={"correo": "pasajera@buscerca.co"}).json()["codigo_demo"]
    malo = "000000" if cod != "000000" else "111111"
    r = api.post("/api/auth/restablecer", json={"correo": "pasajera@buscerca.co", "codigo": malo, "nueva": "NuevaClave77"})
    assert r.status_code == 400
    reloj.fijar(RELOJ + timedelta(minutes=16))
    assert api.post("/api/auth/restablecer", json={"correo": "pasajera@buscerca.co", "codigo": cod, "nueva": "NuevaClave77"}).status_code == 400
    reloj.fijar(RELOJ)
    cod = api.post("/api/auth/recuperar", json={"correo": "pasajera@buscerca.co"}).json()["codigo_demo"]
    assert api.post("/api/auth/restablecer", json={"correo": "pasajera@buscerca.co", "codigo": cod, "nueva": "NuevaClave77"}).status_code == 200
    assert api.post("/api/auth/restablecer", json={"correo": "pasajera@buscerca.co", "codigo": cod, "nueva": "OtraClave88"}).status_code == 400


# ---------------- HU-0104 Edición del perfil ----------------
def test_CP_0104_01_edita_sus_datos(api, datos, sesion):
    h = sesion("pasajera@buscerca.co")
    r = api.patch("/api/perfil", headers=h, json={"nombre": "Ana María Torres", "telefono": "3205550000", "direccion": "Vereda Rodamontal, finca El Roble"})
    assert r.status_code == 200 and r.json()["mensaje"] == "Datos actualizados"
    p = api.get("/api/perfil", headers=h).json()
    assert (p["nombre"], p["telefono"], p["correo"]) == ("Ana María Torres", "3205550000", "pasajera@buscerca.co")


def test_CP_0104_02_valida_y_no_cambia(api, datos, sesion):
    h = sesion("pasajera@buscerca.co")
    assert api.patch("/api/perfil", headers=h, json={"nombre": "Ana Torres", "telefono": "31A"}).status_code == 400
    assert api.patch("/api/perfil", headers=h, json={"nombre": "A"}).status_code == 400
    assert api.get("/api/perfil", headers=h).json()["telefono"] == "3001112233"


def test_CP_0104_03_cambia_contrasena(api, datos, sesion):
    h = sesion("pasajera@buscerca.co")
    r = api.post("/api/perfil/contrasena", headers=h, json={"actual": "Equivocada1", "nueva": "Segura2027"})
    assert r.status_code == 400 and r.json()["detail"] == "La contraseña actual no es correcta"
    assert api.post("/api/perfil/contrasena", headers=h, json={"actual": seed.CLAVE, "nueva": "Segura2027"}).status_code == 200
    assert login(api, "pasajera@buscerca.co", "Segura2027").status_code == 200


# ---------------- HU-0105 Cierre de sesión seguro ----------------
def test_CP_0105_01_cierra_sesion_y_anula_el_token(api, datos, sesion):
    h = sesion("pasajera@buscerca.co")
    assert api.post("/api/auth/logout", headers=h).json()["mensaje"] == "Sesión cerrada"
    r = api.get("/api/perfil", headers=h)
    assert r.status_code == 401 and r.json()["detail"] == "La sesión fue cerrada; inicia sesión de nuevo"


def test_CP_0105_02_sesion_vencida(api, datos, sesion):
    h = sesion("pasajera@buscerca.co")
    reloj.fijar(RELOJ + timedelta(hours=13))
    assert api.get("/api/perfil", headers=h).status_code == 401


def test_CP_0105_03_otra_sesion_no_se_afecta(api, datos, sesion):
    h1, h2 = sesion("pasajera@buscerca.co"), sesion("pasajera@buscerca.co")
    api.post("/api/auth/logout", headers=h1)
    assert api.get("/api/perfil", headers=h2).status_code == 200
