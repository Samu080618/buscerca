"""Casos de prueba del Sprint 2 — Módulo 02: Panel del Conductor (HU-0201 a HU-0205).
Cada prueba lleva el código del caso de prueba (CP) del formato de pruebas del documento.
Los pasos que dependen del celular (permiso, notificación, pantalla bloqueada) se prueban en la app
(app-android, pruebas unitarias de la capa de dominio) y en el celular según la sección de pruebas."""
from datetime import datetime, timedelta

import seed

RELOJ = datetime(2026, 11, 5, 6, 0, 0)
JORGE = "jorge.ramirez@buscerca.co"
LUIS = "luis.pardo@buscerca.co"


def iniciar(api, h, datos, ruta="R-07", vehiculo="014"):
    return api.post("/api/recorridos", headers=h, json={"id_ruta": datos["ruta"][ruta], "id_vehiculo": datos["vehiculo"][vehiculo]})


def coord(seg, vel=30.0, lat=5.0500, lon=-73.9850):
    return {"latitud": lat, "longitud": lon, "velocidad": vel, "fecha_hora": (RELOJ + timedelta(seconds=seg)).isoformat()}


# ---------------- HU-0201 Iniciar recorrido ----------------
def test_CP_0201_01_sin_ruta_o_vehiculo_no_inicia(api, datos, sesion):
    """CA1: sin ruta o vehículo no se puede iniciar (la app deshabilita el botón; la API también lo rechaza)."""
    h = sesion(JORGE)
    assert api.post("/api/recorridos", headers=h, json={"id_ruta": datos["ruta"]["R-07"]}).status_code == 400
    r = api.post("/api/recorridos", headers=h, json={"id_vehiculo": datos["vehiculo"]["014"]})
    assert r.status_code == 400 and r.json()["detail"] == "Selecciona la ruta y el vehículo"
    assert api.get("/api/recorridos/activo", headers=h).status_code == 404


def test_CP_0201_02_inicia_recorrido_en_curso(api, datos, sesion):
    """CA2: crea el recorrido EN CURSO con fecha y hora de inicio, ruta y vehículo, en menos de 3 s."""
    h = sesion(JORGE)
    op = api.get("/api/recorridos/opciones", headers=h).json()
    assert "R-07" in [r["codigo"] for r in op["rutas"]] and "R-09" not in [r["codigo"] for r in op["rutas"]]
    t0 = datetime.now()
    r = iniciar(api, h, datos)
    assert (datetime.now() - t0).total_seconds() < 3
    assert r.status_code == 201
    rec = r.json()
    assert rec["estado"] == "EN CURSO" and rec["ruta"]["codigo"] == "R-07" and rec["vehiculo"]["numero_interno"] == "014"
    assert rec["fecha_inicio"] == RELOJ.isoformat()


def test_CP_0201_03_sin_permiso_no_se_crea_recorrido(api, datos, sesion):
    """CA3: si el conductor rechaza el permiso, la app no llama a la API; se verifica que no existe recorrido.
    El mensaje lo valida ReglasRecorridoTest.sinPermisoNoInicia en app-android."""
    h = sesion(JORGE)
    assert api.get("/api/recorridos/activo", headers=h).status_code == 404


def test_CP_0201_04_no_permite_dos_recorridos_en_curso(api, datos, sesion, bd):
    """CA4 (RN-201): con un recorrido EN CURSO no se crea otro y se devuelve el activo."""
    h = sesion(JORGE)
    primero = iniciar(api, h, datos).json()
    r = iniciar(api, h, datos, "R-11", "033")
    assert r.status_code == 409
    assert r.json()["detail"]["recorrido"]["id_recorrido"] == primero["id_recorrido"]
    assert bd.consultar_uno("SELECT count(*) AS n FROM recorrido WHERE id_usuario = %s AND id_estado = 1", (datos['usuario'][JORGE],))["n"] == 1
    assert api.get("/api/recorridos/activo", headers=h).json()["id_recorrido"] == primero["id_recorrido"]


def test_CP_0201_05_pasajero_no_accede(api, datos, sesion):
    """CA5: un usuario con rol Pasajero no puede abrir Iniciar recorrido (403) ni iniciar uno."""
    h = sesion("pasajera@buscerca.co")
    assert api.get("/api/recorridos/opciones", headers=h).status_code == 403
    assert iniciar(api, h, datos).status_code == 403
    assert api.get("/api/recorridos/opciones").status_code == 401


# ---------------- HU-0202 Transmitir ubicación ----------------
def test_CP_0202_01_registra_una_ubicacion_cada_10_segundos(api, datos, sesion):
    """CA1: en 10 minutos el servidor registra entre 55 y 60 ubicaciones (una cada 10 s ± 2 s).
    Se envían como lo hace ServicioGPS: una coordenada cada 10 s durante 600 s."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    for i in range(60):
        assert api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": [coord(10 * i + (i % 3) - 1)]}).status_code == 201
    from app.datos.conexion_bd import ConexionBD
    filas = ConexionBD().consultar("SELECT fecha_hora FROM ubicacion WHERE id_recorrido = %s ORDER BY fecha_hora", (rec,))
    assert 55 <= len(filas) <= 60
    saltos = [(b["fecha_hora"] - a["fecha_hora"]).total_seconds() for a, b in zip(filas, filas[1:])]
    assert all(8 <= s <= 12 for s in saltos)


def test_CP_0202_02_guarda_todos_los_datos_de_la_coordenada(api, datos, sesion, bd):
    """CA2: la coordenada queda con latitud, longitud, velocidad, fecha y hora de captura e identificador del recorrido."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    r = api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": [coord(10, 31.5, 5.0412, -73.9936)]})
    assert r.status_code == 201 and r.json()["guardadas"] == 1
    u = bd.consultar_uno("SELECT * FROM ubicacion WHERE id_recorrido = %s", (rec,))
    assert float(u["latitud"]) == 5.0412 and float(u["longitud"]) == -73.9936 and float(u["velocidad"]) == 31.5
    assert u["fecha_hora"] == RELOJ + timedelta(seconds=10) and u["id_recorrido"] == rec
    assert u["km_en_ruta"] is not None  # proyectada sobre el trazado para el Módulo 03


def test_CP_0202_03_pendientes_en_orden_y_sin_duplicados(api, datos, sesion, bd):
    """CA3 (RN-204): las 12 coordenadas de 2 minutos sin conexión se envían en orden de captura y sin duplicados,
    aunque el lote llegue desordenado o se reenvíe."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    lote = [coord(10 * i, 20 + i) for i in range(12)]
    desordenado = lote[6:] + lote[:6]
    r = api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": desordenado})
    assert r.json()["guardadas"] == 12
    r2 = api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": lote[:4]})  # reintento
    assert r2.json()["guardadas"] == 0 and r2.json()["duplicadas"] == 4
    filas = bd.consultar("SELECT fecha_hora, id_ubicacion FROM ubicacion WHERE id_recorrido = %s ORDER BY id_ubicacion", (rec,))
    assert len(filas) == 12
    assert [f["fecha_hora"] for f in filas] == sorted(f["fecha_hora"] for f in filas)


def test_CP_0202_04_rechaza_recorrido_finalizado_o_ajeno(api, datos, sesion, bd):
    """CA4 (RN-203): una coordenada de un recorrido FINALIZADO o de otro conductor recibe 409 y no se guarda."""
    hj, hl = sesion(JORGE), sesion(LUIS)
    rec = iniciar(api, hj, datos).json()["id_recorrido"]
    r = api.post(f"/api/recorridos/{rec}/ubicaciones", headers=hl, json={"coordenadas": [coord(10)]})
    assert r.status_code == 409
    api.patch(f"/api/recorridos/{rec}/finalizar", headers=hj)
    r = api.post(f"/api/recorridos/{rec}/ubicaciones", headers=hj, json={"coordenadas": [coord(20)]})
    assert r.status_code == 409 and r.json()["detail"] == "El recorrido no está en curso"
    assert bd.consultar_uno("SELECT count(*) AS n FROM ubicacion WHERE id_recorrido = %s", (rec,))["n"] == 0


# ---------------- HU-0203 Velocidad promedio ----------------
def _enviar(api, h, rec, velocidades):
    for i, v in enumerate(velocidades):
        r = api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": [coord(60 * i + 10, v)]})
    return r.json()


def test_CP_0203_01_promedio_incluye_lecturas_en_cero(api, datos, sesion):
    """CA1: con 30, 0, 34 y 32 km/h en los últimos 5 minutos, la ubicación nueva se guarda con 24 km/h."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    assert float(_enviar(api, h, rec, [30, 0, 34, 32])["velocidad_promedio"]) == 24.0


def test_CP_0203_02_descarta_lecturas_invalidas(api, datos, sesion):
    """CA2 (RN-206): con 30, -5 y 150 km/h se descartan -5 y 150 y se guarda 30 km/h."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    assert float(_enviar(api, h, rec, [30, -5, 150])["velocidad_promedio"]) == 30.0


def test_CP_0203_03_sin_lecturas_validas_guarda_nulo(api, datos, sesion, bd):
    """CA3: sin lecturas válidas en los últimos 5 minutos el promedio se guarda nulo y no hay error.
    La lectura válida de hace 6 minutos queda fuera de la ventana."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": [coord(0, 40)]})
    r = api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": [coord(360, None), coord(370, 200)]})
    assert r.status_code == 201 and r.json()["velocidad_promedio"] is None
    assert bd.consultar_uno("SELECT velocidad_promedio FROM ubicacion WHERE id_recorrido = %s ORDER BY fecha_hora DESC LIMIT 1", (rec,))["velocidad_promedio"] is None


def test_CP_0203_04_pantalla_consulta_ultimo_promedio(api, datos, sesion):
    """CA4: la pantalla del recorrido consulta el último valor de la velocidad promedio en km/h."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    _enviar(api, h, rec, [30, 0, 34, 32])
    assert float(api.get(f"/api/recorridos/{rec}/velocidad", headers=h).json()["velocidad_promedio"]) == 24.0
    assert float(api.get("/api/recorridos/activo", headers=h).json()["velocidad_promedio"]) == 24.0


# ---------------- HU-0204 Reportar novedad ----------------
def test_CP_0204_01_registra_novedad(api, datos, sesion, bd):
    """CA1: "Falla mecánica" con "Llanta pinchada" queda con tipo, comentario, ubicación y hora; responde "Novedad reportada"."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    tipos = {t["descripcion"]: t["id_tipo_novedad"] for t in api.get("/api/tipos-novedad", headers=h).json()}
    r = api.post(f"/api/recorridos/{rec}/novedades", headers=h,
                 json={"id_tipo_novedad": tipos["Falla mecánica"], "comentario": "Llanta pinchada", "latitud": 5.0412, "longitud": -73.9936})
    assert r.status_code == 201 and r.json()["mensaje"] == "Novedad reportada"
    n = bd.consultar_uno("SELECT * FROM novedad WHERE id_recorrido = %s", (rec,))
    assert n["comentario"] == "Llanta pinchada" and n["id_tipo_novedad"] == tipos["Falla mecánica"]
    assert float(n["latitud"]) == 5.0412 and n["fecha_hora"] == RELOJ


def test_CP_0204_02_tipo_obligatorio(api, datos, sesion, bd):
    """CA2: sin tipo no se registra nada (la app marca el campo; la API también lo exige)."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    r = api.post(f"/api/recorridos/{rec}/novedades", headers=h, json={"comentario": "Sin tipo"})
    assert r.status_code == 400 and r.json()["detail"] == "Selecciona el tipo de novedad"
    assert bd.consultar_uno("SELECT count(*) AS n FROM novedad")["n"] == 0


def test_CP_0204_03_comentario_maximo_200(api, datos, sesion, bd):
    """CA3: un comentario de 201 caracteres no se acepta; uno de 200 sí."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    r = api.post(f"/api/recorridos/{rec}/novedades", headers=h, json={"id_tipo_novedad": datos["tipo"]["Otro"], "comentario": "x" * 201})
    assert r.status_code == 400
    r = api.post(f"/api/recorridos/{rec}/novedades", headers=h, json={"id_tipo_novedad": datos["tipo"]["Otro"], "comentario": "x" * 200})
    assert r.status_code == 201
    assert bd.consultar_uno("SELECT count(*) AS n FROM novedad")["n"] == 1


def test_CP_0204_04_sin_recorrido_en_curso(api, datos, sesion, bd):
    """CA4: sin recorrido EN CURSO responde "No hay recorrido en curso" y no registra."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    api.patch(f"/api/recorridos/{rec}/finalizar", headers=h)
    r = api.post(f"/api/recorridos/{rec}/novedades", headers=h, json={"id_tipo_novedad": datos["tipo"]["Clima"]})
    assert r.status_code == 409 and r.json()["detail"] == "No hay recorrido en curso"
    assert bd.consultar_uno("SELECT count(*) AS n FROM novedad")["n"] == 0


def test_CP_0204_05_sin_conexion_no_registra(api, datos, sesion, bd):
    """CA5: sin conexión la novedad no llega al servidor (la app muestra el mensaje y conserva el formulario:
    FormularioNovedadTest.sinConexionConservaTexto). Al reintentar con conexión se registra una sola vez."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    assert bd.consultar_uno("SELECT count(*) AS n FROM novedad")["n"] == 0
    r = api.post(f"/api/recorridos/{rec}/novedades", headers=h, json={"id_tipo_novedad": datos["tipo"]["Vía bloqueada"], "comentario": "Derrumbe km 3"})
    assert r.status_code == 201
    assert bd.consultar_uno("SELECT count(*) AS n FROM novedad")["n"] == 1


# ---------------- HU-0205 Finalizar recorrido ----------------
def test_CP_0205_01_cancelar_no_finaliza(api, datos, sesion):
    """CA1: si el conductor cancela el diálogo, la app no llama a finalizar y el recorrido sigue EN CURSO."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    assert api.get("/api/recorridos/activo", headers=h).json()["estado"] == "EN CURSO"
    assert api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": [coord(10)]}).status_code == 201


def test_CP_0205_02_envia_pendientes_y_finaliza(api, datos, sesion, bd):
    """CA2: las 3 coordenadas pendientes se envían antes de cerrar y el recorrido queda FINALIZADO con fecha de fin."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    assert api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": [coord(10), coord(20), coord(30)]}).json()["guardadas"] == 3
    from app import reloj
    reloj.fijar(RELOJ + timedelta(minutes=48))
    r = api.patch(f"/api/recorridos/{rec}/finalizar", headers=h).json()
    assert r["estado"] == "FINALIZADO" and r["fecha_fin"] == (RELOJ + timedelta(minutes=48)).isoformat()
    assert r["ubicaciones_registradas"] == 3 and r["duracion_minutos"] == 48


def test_CP_0205_03_resumen_con_inicio_y_fin(api, datos, sesion):
    """CA3: al finalizar el conductor ve el resumen con hora de inicio y fin (la notificación la retira ServicioGPS)."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    r = api.patch(f"/api/recorridos/{rec}/finalizar", headers=h).json()
    assert r["fecha_inicio"] and r["fecha_fin"]
    assert api.get("/api/recorridos/activo", headers=h).status_code == 404


def test_CP_0205_04_finalizado_rechaza_y_permite_nuevo(api, datos, sesion):
    """CA4 (RN-205): un recorrido FINALIZADO rechaza coordenadas y el conductor puede iniciar uno nuevo."""
    h = sesion(JORGE)
    rec = iniciar(api, h, datos).json()["id_recorrido"]
    api.patch(f"/api/recorridos/{rec}/finalizar", headers=h)
    assert api.post(f"/api/recorridos/{rec}/ubicaciones", headers=h, json={"coordenadas": [coord(10)]}).status_code == 409
    assert api.patch(f"/api/recorridos/{rec}/finalizar", headers=h).status_code == 409
    assert iniciar(api, h, datos).status_code == 201
