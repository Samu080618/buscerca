"""Casos de prueba del Sprint 3 — Módulo 03: Panel del Pasajero (HU-0301 a HU-0305).
Reloj fijo: jueves 19/11/2026 07:00. Pasajera de prueba a 350 m del paradero Cogua centro."""
import json
from datetime import datetime, timedelta

import seed

RELOJ = datetime(2026, 11, 19, 7, 0, 0)
PASAJERA = "pasajera@buscerca.co"
LAT, LON = 5.0641, -73.9790          # a ~350 m de Cogua centro
CONDUCTORES = {"014": "jorge.ramirez@buscerca.co", "021": "luis.pardo@buscerca.co", "009": "martha.rojas@buscerca.co"}


def bus(bd, datos, num, ruta, km_antes_de_cogua, vel, hace=timedelta(seconds=5)):
    """Crea un recorrido EN CURSO del vehículo y lo ubica a km_antes_de_cogua del paradero Cogua centro."""
    id_r = datos["ruta"][ruta]
    rec = bd.consultar_uno("INSERT INTO recorrido (id_usuario, id_vehiculo, id_ruta, id_estado, fecha_inicio) VALUES (%s, %s, %s, 1, %s) RETURNING id_recorrido",
                           (datos["usuario"][CONDUCTORES[num]], datos["vehiculo"][num], id_r, RELOJ - timedelta(minutes=20)))["id_recorrido"]
    seed.poner_bus(bd, rec, seed.km_paradero(bd, id_r, datos["paradero"]["COG"]) - km_antes_de_cogua, vel, RELOJ - hace)
    bd.confirmar()
    return rec


def buscar(api, h, texto):
    return api.get("/api/rutas/buscar", headers=h, params={"texto": texto, "lat": LAT, "lon": LON})


# ---------------- HU-0301 Buscar rutas por destino ----------------
def test_CP_0301_01_busca_rutas_activas_con_abordaje(api, datos, sesion, bd):
    """CA1: "rodamontal" desde Cogua centro devuelve R-07 y R-11 con abordaje, sentido y vehículos, en menos de 3 s."""
    bus(bd, datos, "014", "R-07", 4.3, 32)
    h = sesion(PASAJERA)
    t0 = datetime.now()
    r = buscar(api, h, "rodamontal")
    assert (datetime.now() - t0).total_seconds() < 3 and r.status_code == 200
    res = {x["codigo"]: x for x in r.json()["resultados"]}
    assert set(res) == {"R-07", "R-11"}
    assert res["R-07"]["abordaje"]["nombre"] == "Cogua centro" and res["R-07"]["abordaje"]["metros"] < 400
    assert res["R-07"]["sentido"] == "Zipaquirá → El Mortiño"
    assert res["R-07"]["vehiculos_operando"] == 1 and res["R-11"]["vehiculos_operando"] == 0


def test_CP_0301_02_menos_de_3_letras(api, datos, sesion):
    """CA2 (RN-301): "Ro" se rechaza con "Escribe al menos 3 letras" (la app no envía la petición:
    ValidadorBusquedaTest; la API también lo valida)."""
    h = sesion(PASAJERA)
    for texto in ["Ro", "  r ", "12345", "R-0"]:
        r = buscar(api, h, texto)
        assert r.status_code == 400 and r.json()["detail"] == "Escribe al menos 3 letras"


def test_CP_0301_03_excluye_inactivas_y_destino_antes_del_abordaje(api, datos, sesion):
    """CA3 (RN-302): R-09 (Inactiva) y R-05 (Rodamontal antes de Cogua centro) no aparecen."""
    h = sesion(PASAJERA)
    codigos = [x["codigo"] for x in buscar(api, h, "Rodamontal").json()["resultados"]]
    assert "R-09" not in codigos and "R-05" not in codigos


def test_CP_0301_04_ordena_por_proximo_bus(api, datos, sesion, bd):
    """CA4 (RN-304): R-07 queda primera con "Bus 014 llega en 8 min" hasta el paradero de abordaje."""
    bus(bd, datos, "014", "R-07", 4.3, 32)
    bus(bd, datos, "021", "R-11", 4.9, 30)
    h = sesion(PASAJERA)
    res = buscar(api, h, "Rodamontal").json()["resultados"]
    assert res[0]["codigo"] == "R-07"
    assert res[0]["proximo_bus"]["indicador"] == "Bus 014 llega en 8 min"
    assert res[1]["proximo_bus"]["indicador"] == "Bus 021 llega en 10 min"


def test_CP_0301_05_destino_inexistente(api, datos, sesion):
    """CA5: "La Cabaña" responde "No encontramos rutas hacia La Cabaña" en menos de 3 s y por debajo de 500 KB."""
    h = sesion(PASAJERA)
    t0 = datetime.now()
    r = buscar(api, h, "La Cabaña")
    assert (datetime.now() - t0).total_seconds() < 3
    assert r.status_code == 200 and r.json()["resultados"] == []
    assert r.json()["mensaje"] == "No encontramos rutas hacia La Cabaña"
    assert len(r.content) < 500 * 1024


# ---------------- HU-0302 Ver el bus en el mapa ----------------
def test_CP_0302_01_mapa_con_trazado_paraderos_y_bus(api, datos, sesion, bd):
    """CA1: R-07 devuelve la polilínea, sus 5 paraderos y el Bus 014 en su última coordenada con ETA."""
    rec = bus(bd, datos, "014", "R-07", 4.3, 32)
    h = sesion(PASAJERA)
    r07, cog = datos["ruta"]["R-07"], datos["paradero"]["COG"]
    t = api.get(f"/api/rutas/{r07}/trazado", headers=h).json()
    assert len(t["trazado"]) >= 2 and [p["nombre"] for p in t["paraderos"]][2] == "Cogua centro" and len(t["paraderos"]) == 5
    b = api.get(f"/api/rutas/{r07}/buses", headers=h, params={"paradero": cog}).json()["buses"]
    ult = bd.consultar_uno("SELECT latitud, longitud FROM ubicacion WHERE id_recorrido = %s", (rec,))
    assert b[0]["numero_interno"] == "014" and b[0]["senal"] == "ACTIVA"
    assert (b[0]["latitud"], b[0]["longitud"]) == (float(ult["latitud"]), float(ult["longitud"]))
    assert b[0]["eta"]["texto"] == "8 min"


def test_CP_0302_02_actualiza_posicion_en_menos_de_20_s(api, datos, sesion, bd):
    """CA2 (RN-305): la app consulta cada 10 s; una coordenada nueva del conductor aparece en la siguiente consulta."""
    rec = bus(bd, datos, "014", "R-07", 4.3, 32)
    hp, hc = sesion(PASAJERA), sesion(CONDUCTORES["014"])
    r07 = datos["ruta"]["R-07"]
    antes = api.get(f"/api/rutas/{r07}/buses", headers=hp).json()
    assert antes["refresco_segundos"] == 10
    nueva = {"latitud": 5.0500, "longitud": -73.9870, "velocidad": 33, "fecha_hora": RELOJ.isoformat()}
    assert api.post(f"/api/recorridos/{rec}/ubicaciones", headers=hc, json={"coordenadas": [nueva]}).status_code == 201
    despues = api.get(f"/api/rutas/{r07}/buses", headers=hp).json()["buses"][0]
    assert (despues["latitud"], despues["longitud"]) == (5.05, -73.987)
    assert despues["latitud"] != antes["buses"][0]["latitud"]


def test_CP_0302_03_bus_sin_senal_en_gris_y_oculto(api, datos, sesion, bd):
    """CA3 (RN-306): con 5 min sin señal el Bus 021 sale gris con "Sin señal desde 06:55"; con 15 min o más no se muestra."""
    bus(bd, datos, "021", "R-07", 2.0, 30, hace=timedelta(minutes=5))
    h = sesion(PASAJERA)
    r07 = datos["ruta"]["R-07"]
    b = api.get(f"/api/rutas/{r07}/buses", headers=h).json()["buses"][0]
    assert b["senal"] == "SIN_SENAL" and b["etiqueta"] == "Sin señal desde 06:55"
    from app import reloj
    reloj.fijar(RELOJ + timedelta(minutes=10))     # ahora lleva 15 minutos sin señal
    assert api.get(f"/api/rutas/{r07}/buses", headers=h).json()["buses"] == []
    reloj.fijar(RELOJ + timedelta(minutes=11))     # 16 minutos
    assert api.get(f"/api/rutas/{r07}/buses", headers=h).json()["buses"] == []


def test_CP_0302_04_sin_buses_muestra_proxima_salida(api, datos, sesion):
    """CA4: R-11 sin buses en curso muestra el trazado, los paraderos y la próxima salida 07:40."""
    h = sesion(PASAJERA)
    r11 = datos["ruta"]["R-11"]
    assert len(api.get(f"/api/rutas/{r11}/trazado", headers=h).json()["paraderos"]) == 4
    r = api.get(f"/api/rutas/{r11}/buses", headers=h)
    assert r.json()["mensaje"] == "No hay buses en camino" and r.json()["proxima_salida"] == "07:40"
    assert len(r.content) < 500 * 1024


# ---------------- HU-0303 Datos del vehículo ----------------
def test_CP_0303_01_ficha_con_los_7_datos(api, datos, sesion, bd):
    """CA1 (RN-307): número 014, placa WXK 382, tipo, empresa, conductor Jorge Ramírez, hora de salida y estado."""
    rec = bus(bd, datos, "014", "R-07", 4.3, 32)
    h = sesion(PASAJERA)
    r = api.get(f"/api/recorridos/{rec}/ficha", headers=h)
    f = r.json()
    assert f["numero_interno"] == "014" and f["placa"] == "WXK 382" and f["tipo"] == "Bus"
    assert f["empresa"] == "Cooperativa de Transportes Zipaquirá" and f["conductor"]["nombre"] == "Jorge Ramírez"
    assert f["hora_salida"] == "06:40" and f["estado"].startswith("En curso")
    assert len(r.content) < 500 * 1024


def test_CP_0303_02_no_expone_datos_personales(api, datos, sesion, bd):
    """CA2 (RN-307): el conductor solo trae nombre y foto; nunca documento, teléfono ni dirección."""
    rec = bus(bd, datos, "014", "R-07", 4.3, 32)
    h = sesion(PASAJERA)
    r = api.get(f"/api/recorridos/{rec}/ficha", headers=h)
    assert set(r.json()["conductor"]) == {"nombre", "foto_url"}
    for dato in ["79845123", "3104567890", "Cra 7", "documento", "telefono", "direccion"]:
        assert dato not in r.text
    for path in [f"/api/rutas/{datos['ruta']['R-07']}/buses", "/api/rutas/buscar?texto=rodamontal&lat=5.0641&lon=-73.979"]:
        assert "79845123" not in api.get(path, headers=h).text


def test_CP_0303_03_recorrido_terminado(api, datos, sesion, bd):
    """CA3: si el recorrido acaba de pasar a FINALIZADO, la ficha responde "Este recorrido ya terminó" (410)."""
    rec = bus(bd, datos, "014", "R-07", 4.3, 32)
    api.patch(f"/api/recorridos/{rec}/finalizar", headers=sesion(CONDUCTORES["014"]))
    r = api.get(f"/api/recorridos/{rec}/ficha", headers=sesion(PASAJERA))
    assert r.status_code == 410 and r.json()["detail"] == "Este recorrido ya terminó"
    assert api.get(f"/api/rutas/{datos['ruta']['R-07']}/buses", headers=sesion(PASAJERA)).json()["buses"] == []


# ---------------- HU-0304 Tiempo de llegada ----------------
def llegadas(api, h, datos, ruta="R-07"):
    return api.get(f"/api/paraderos/{datos['paradero']['COG']}/llegadas", headers=h, params={"ruta": datos["ruta"][ruta]}).json()


def test_CP_0304_01_eta_8_minutos(api, datos, sesion, bd):
    """CA1: a 4,3 km con 32 km/h muestra "8 min" (la exactitud de ±3 min se mide en la prueba de campo del Sprint 4)."""
    bus(bd, datos, "014", "R-07", 4.3, 32)
    l = llegadas(api, sesion(PASAJERA), datos)["llegadas"][0]
    assert l["eta"]["texto"] == "8 min" and l["eta"]["estado"] == "EN_CAMINO"


def test_CP_0304_02_llegando(api, datos, sesion, bd):
    """CA2: a 0,6 km con 28 km/h (1,3 min) muestra "Llegando"."""
    bus(bd, datos, "021", "R-07", 0.6, 28)
    l = llegadas(api, sesion(PASAJERA), datos)["llegadas"][0]
    assert l["eta"]["texto"] == "Llegando" and l["eta"]["minutos"] == 1.3


def test_CP_0304_03_ya_paso(api, datos, sesion, bd):
    """CA3 (RN-309): el Bus 009 con km en ruta mayor que el del paradero muestra "Ya pasó", no un tiempo negativo."""
    bus(bd, datos, "009", "R-07", -1.2, 27)
    l = llegadas(api, sesion(PASAJERA), datos)["llegadas"][0]
    assert l["numero_interno"] == "009" and l["eta"]["texto"] == "Ya pasó" and l["eta"]["minutos"] is None


def test_CP_0304_04_velocidad_historica_aprox(api, datos, sesion, bd):
    """CA4 (RN-308): con 2 km/h usa la velocidad histórica de 25 km/h y añade "aprox."."""
    bus(bd, datos, "014", "R-07", 4.3, 2)
    e = llegadas(api, sesion(PASAJERA), datos)["llegadas"][0]["eta"]
    assert e["aproximado"] is True and e["texto"] == "10 min aprox."


def test_CP_0304_05_sin_buses_en_camino(api, datos, sesion, bd):
    """CA5: sin buses antes del paradero muestra "No hay buses en camino" y la próxima salida 07:40."""
    bus(bd, datos, "021", "R-11", -2.0, 30)   # uno que ya pasó no cuenta como "en camino"
    r = llegadas(api, sesion(PASAJERA), datos, "R-11")
    assert r["mensaje"] == "No hay buses en camino" and r["proxima_salida"] == "07:40"
    assert len(json.dumps(r)) < 500 * 1024


# ---------------- HU-0305 Favoritos ----------------
def favoritos_previos(bd, datos, n, correo=PASAJERA):
    combos = [(c, p) for c in ["R-03", "R-05", "R-07", "R-11"] for p in [None, "COG"]] + [(None, "ROD"), (None, "MOR"), (None, "ZIP")]
    for c, p in combos[:n]:
        bd.ejecutar("INSERT INTO favorito (id_pasajero, tipo, id_ruta, id_paradero, alias, fecha_creacion) VALUES (%s, %s, %s, %s, %s, %s)",
                    (datos["usuario"][correo], "RUTA" if c else "PARADERO", c and datos["ruta"][c], p and datos["paradero"][p], None, RELOJ - timedelta(days=3)))
    bd.confirmar()


def nuevo_fav(api, h, datos, alias="Bus para ir a la finca"):
    return api.post("/api/favoritos", headers=h, json={"tipo": "RUTA", "id_ruta": datos["ruta"]["R-07"], "id_paradero": datos["paradero"]["ROD"], "alias": alias})


def test_CP_0305_01_guarda_favorito(api, datos, sesion, bd):
    """CA1: con 4 favoritos, guardar R-07 con "Bus para ir a la finca" deja 5 y permite abrir el mapa de esa ruta."""
    favoritos_previos(bd, datos, 4)
    h = sesion(PASAJERA)
    r = nuevo_fav(api, h, datos)
    assert r.status_code == 201 and r.json()["alias"] == "Bus para ir a la finca"
    lista = api.get("/api/favoritos", headers=h).json()
    assert len(lista) == 5
    assert api.get(f"/api/rutas/{lista[-1]['id_ruta']}/trazado", headers=h).json()["codigo"] == "R-07"


def test_CP_0305_02_maximo_10(api, datos, sesion, bd):
    """CA2 (RN-310): con 10 favoritos, el 11 se rechaza con el mensaje de límite y no se crea."""
    favoritos_previos(bd, datos, 10)
    h = sesion(PASAJERA)
    r = nuevo_fav(api, h, datos)
    assert r.status_code == 409 and r.json()["detail"].startswith("Llegaste al máximo de 10 favoritos")
    assert len(api.get("/api/favoritos", headers=h).json()) == 10


def test_CP_0305_03_no_repetidos(api, datos, sesion):
    """CA3 (RN-310): guardar otra vez R-07 con el mismo paradero responde "Ya está en tus favoritos"."""
    h = sesion(PASAJERA)
    nuevo_fav(api, h, datos)
    r = nuevo_fav(api, h, datos, "Otra vez")
    assert r.status_code == 409 and r.json()["detail"] == "Ya está en tus favoritos"
    assert len(api.get("/api/favoritos", headers=h).json()) == 1


def test_CP_0305_04_alias_maximo_30(api, datos, sesion):
    """CA4: renombrar con 31 caracteres se rechaza y conserva el alias anterior."""
    h = sesion(PASAJERA)
    f = nuevo_fav(api, h, datos).json()
    r = api.patch(f"/api/favoritos/{f['id_favorito']}", headers=h, json={"alias": "x" * 31})
    assert r.status_code == 400 and r.json()["detail"] == "El alias admite máximo 30 caracteres"
    assert api.get(f"/api/favoritos/{f['id_favorito']}", headers=h).json()["alias"] == "Bus para ir a la finca"
    assert api.patch(f"/api/favoritos/{f['id_favorito']}", headers=h, json={"alias": "x" * 30}).status_code == 200


def test_CP_0305_05_favorito_ajeno_404(api, datos, sesion, bd):
    """CA5 (RN-311): consultar, renombrar o eliminar un favorito de otro usuario responde 404 y no lo modifica."""
    ajeno = nuevo_fav(api, sesion("pasajero2@buscerca.co"), datos).json()["id_favorito"]
    h = sesion(PASAJERA)
    assert api.get(f"/api/favoritos/{ajeno}", headers=h).status_code == 404
    assert api.patch(f"/api/favoritos/{ajeno}", headers=h, json={"alias": "mío"}).status_code == 404
    r = api.delete(f"/api/favoritos/{ajeno}", headers=h)
    assert r.status_code == 404 and len(r.content) < 500 * 1024
    f = bd.consultar_uno("SELECT alias FROM favorito WHERE id_favorito = %s", (ajeno,))
    assert f is not None and f["alias"] == "Bus para ir a la finca"
