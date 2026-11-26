"""Crea el esquema y carga los datos iniciales de BusCerca (rutas, paraderos, vehículos y usuarios de prueba).

Uso:  python seed.py            → base definida en DATABASE_URL
      python seed.py --demo     → además deja buses en curso para la demostración (ver simulador.py)
      python seed.py --demo --si-vacia → solo carga si la base está vacía (lo usa Render al arrancar)
Los datos de rutas y paraderos reemplazan, mientras se construye el Módulo 05, la administración de rutas.
"""
import pathlib
import sys
from datetime import datetime, timedelta

from app import reloj
from app.control.control_busqueda import normalizar
from app.datos.conexion_bd import ConexionBD
from app.entidades.usuario import Usuario

ESQUEMA = pathlib.Path(__file__).resolve().parent.parent / "database" / "01_esquema.sql"
MODULO01 = ESQUEMA.with_name("02_modulo01.sql")
CLAVE = "BusCerca2026*"

PARADEROS = {  # clave: (nombre, vereda, municipio, lat, lon)
    "ZIP": ("Terminal Zipaquirá", None, "Zipaquirá", 5.0230, -74.0040),
    "BAR": ("Barandillas", "Barandillas", "Zipaquirá", 5.0420, -73.9930),
    "COG": ("Cogua centro", None, "Cogua", 5.0610, -73.9790),
    "ROD": ("Rodamontal", "Rodamontal", "Cogua", 5.0900, -73.9650),
    "MOR": ("El Mortiño", "El Mortiño", "Cogua", 5.1180, -73.9480),
    "PLA": ("La Plazuela", "La Plazuela", "Cogua", 5.0750, -73.9920),
    "NEU": ("Embalse del Neusa", "Neusa", "Cogua", 5.1450, -73.9700),
}
RUTAS = [  # codigo, nombre, origen, destino, velocidad histórica, estado, paraderos en orden
    ("R-03", "Cogua – Neusa", "Cogua", "Neusa", 22, "Activa", ["COG", "PLA", "NEU"]),
    ("R-05", "El Mortiño – Zipaquirá", "El Mortiño", "Zipaquirá", 25, "Activa", ["MOR", "ROD", "COG", "BAR", "ZIP"]),
    ("R-07", "Zipaquirá – El Mortiño", "Zipaquirá", "El Mortiño", 25, "Activa", ["ZIP", "BAR", "COG", "ROD", "MOR"]),
    ("R-09", "Cogua – Rodamontal por La Plazuela", "Cogua", "Rodamontal", 20, "Inactiva", ["COG", "PLA", "ROD"]),
    ("R-11", "Zipaquirá – Rodamontal", "Zipaquirá", "Rodamontal", 25, "Activa", ["ZIP", "BAR", "COG", "ROD"]),
]
VEHICULOS = [("WXK382", "014", "Bus", "Cooperativa de Transportes Zipaquirá"),
             ("SXT640", "021", "Colectivo", "Cooperativa de Transportes Zipaquirá"),
             ("TKM215", "009", "Bus", "Transportes Cogua Rural"),
             ("WFD118", "033", "Escalera", "Transportes Cogua Rural")]
USUARIOS = [  # nombre, correo, rol, documento, telefono, direccion
    ("Jorge Ramírez", "jorge.ramirez@buscerca.co", "CONDUCTOR", "79845123", "3104567890", "Cra 7 # 3-21, Cogua"),
    ("Luis Pardo", "luis.pardo@buscerca.co", "CONDUCTOR", "80123456", "3112223344", "Vereda Barandillas, Zipaquirá"),
    ("Martha Rojas", "martha.rojas@buscerca.co", "CONDUCTOR", "52987654", "3205556677", "Calle 4 # 2-10, Cogua"),
    ("Ana Torres", "pasajera@buscerca.co", "PASAJERO", "1076543210", "3001112233", "Vereda Rodamontal"),
    ("Pedro Gómez", "pasajero2@buscerca.co", "PASAJERO", "1076000001", "3001110000", "Cogua"),
    ("Administrador BusCerca", "admin@buscerca.co", "ADMINISTRADOR", None, None, None),
]
TIPOS_NOVEDAD = ["Falla mecánica", "Retraso por tráfico", "Vía bloqueada", "Accidente", "Clima", "Otro"]


def sembrar(bd: ConexionBD, hoy: datetime | None = None) -> dict:
    """Carga el esquema y los datos iniciales. Devuelve los ids creados para usarlos en las pruebas."""
    hoy = (hoy or reloj.ahora()).replace(hour=0, minute=0, second=0, microsecond=0)
    bd.ejecutar(ESQUEMA.read_text(encoding="utf-8"))
    bd.ejecutar(MODULO01.read_text(encoding="utf-8"))
    ids = {"paradero": {}, "ruta": {}, "vehiculo": {}, "usuario": {}, "tipo": {}}
    for t in TIPOS_NOVEDAD:
        ids["tipo"][t] = bd.consultar_uno("INSERT INTO tipo_novedad (descripcion) VALUES (%s) RETURNING id_tipo_novedad", (t,))["id_tipo_novedad"]
    for k, (nombre, vereda, mun, lat, lon) in PARADEROS.items():
        ids["paradero"][k] = bd.consultar_uno(
            """INSERT INTO paradero (nombre, nombre_normalizado, vereda, municipio, latitud, longitud, posicion)
               VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) RETURNING id_paradero""",
            (nombre, normalizar(nombre), vereda, mun, lat, lon, lon, lat))["id_paradero"]
    for cod, nombre, ori, des, vh, estado, pars in RUTAS:
        wkt = "LINESTRING(" + ", ".join(f"{PARADEROS[p][4]} {PARADEROS[p][3]}" for p in pars) + ")"
        id_r = bd.consultar_uno(
            """INSERT INTO ruta (codigo, nombre, origen, destino, trazado, velocidad_historica_kmh, estado)
               VALUES (%s, %s, %s, %s, ST_GeogFromText(%s), %s, %s) RETURNING id_ruta""",
            (cod, nombre, ori, des, "SRID=4326;" + wkt, vh, estado))["id_ruta"]
        ids["ruta"][cod] = id_r
        for orden, p in enumerate(pars, 1):
            bd.ejecutar(
                """INSERT INTO ruta_paradero (id_ruta, id_paradero, orden, km_desde_inicio)
                   SELECT %s, p.id_paradero, %s, round((ST_LineLocatePoint(r.trazado::geometry, p.posicion::geometry) * ST_Length(r.trazado) / 1000)::numeric, 2)
                   FROM ruta r, paradero p WHERE r.id_ruta = %s AND p.id_paradero = %s""",
                (id_r, orden, id_r, ids["paradero"][p]))
    for placa, num, tipo, emp in VEHICULOS:
        ids["vehiculo"][num] = bd.consultar_uno(
            "INSERT INTO vehiculo (placa, numero_interno, tipo, empresa) VALUES (%s, %s, %s, %s) RETURNING id_vehiculo",
            (placa, num, tipo, emp))["id_vehiculo"]
    for nombre, correo, rol, doc, tel, dirc in USUARIOS:
        foto = f"https://buscerca.co/fotos/{correo.split('@')[0]}.jpg" if rol == "CONDUCTOR" else None
        ids["usuario"][correo] = Usuario.crear(bd, nombre, correo, CLAVE, rol, doc, tel, dirc, foto)
    # Salidas programadas del día (RN-304 y CP-0302-04 / CP-0304-05)
    for cod, hora, num, cond in [("R-07", "07:30", "033", "martha.rojas@buscerca.co"), ("R-11", "07:40", "021", "luis.pardo@buscerca.co"),
                                 ("R-03", "08:00", "009", "martha.rojas@buscerca.co"), ("R-05", "08:15", "033", "luis.pardo@buscerca.co")]:
        h, m = map(int, hora.split(":"))
        bd.ejecutar("INSERT INTO recorrido (id_usuario, id_vehiculo, id_ruta, id_estado, fecha_inicio) VALUES (%s, %s, %s, 3, %s)",
                    (ids["usuario"][cond], ids["vehiculo"][num], ids["ruta"][cod], hoy + timedelta(hours=h, minutes=m)))
    return ids


def poner_bus(bd: ConexionBD, id_recorrido: int, km: float, velocidad_promedio: float | None, fecha_hora: datetime):
    """Ubica un recorrido en el kilómetro indicado de su trazado (lo usan la demostración y las pruebas)."""
    bd.ejecutar(
        """INSERT INTO ubicacion (id_recorrido, latitud, longitud, posicion, velocidad, velocidad_promedio, km_en_ruta, fecha_hora)
           SELECT r.id_recorrido, round(ST_Y(pt)::numeric, 6), round(ST_X(pt)::numeric, 6), pt::geography, %(v)s, %(v)s, %(km)s, %(f)s
           FROM recorrido r JOIN ruta ru USING (id_ruta),
                LATERAL (SELECT ST_LineInterpolatePoint(ru.trazado::geometry, GREATEST(0, LEAST(1, %(km)s * 1000 / ST_Length(ru.trazado)))) AS pt) x
           WHERE r.id_recorrido = %(r)s""",
        {"r": id_recorrido, "km": km, "v": velocidad_promedio, "f": fecha_hora})


def km_paradero(bd, id_ruta, id_paradero) -> float:
    return float(bd.consultar_uno("SELECT km_desde_inicio FROM ruta_paradero WHERE id_ruta = %s AND id_paradero = %s", (id_ruta, id_paradero))["km_desde_inicio"])


def demo(bd: ConexionBD, ids: dict):
    """Deja el bus 014 (Jorge Ramírez) y el 009 (Martha Rojas) en curso por la R-07 para la demostración."""
    ahora = reloj.ahora()
    r07, cog = ids["ruta"]["R-07"], ids["paradero"]["COG"]
    for num, correo, km_antes, vel in [("014", "jorge.ramirez@buscerca.co", 4.3, 32), ("009", "martha.rojas@buscerca.co", -1.2, 27)]:
        id_rec = bd.consultar_uno("INSERT INTO recorrido (id_usuario, id_vehiculo, id_ruta, id_estado, fecha_inicio) VALUES (%s, %s, %s, 1, %s) RETURNING id_recorrido",
                                  (ids["usuario"][correo], ids["vehiculo"][num], r07, ahora - timedelta(minutes=25)))["id_recorrido"]
        poner_bus(bd, id_rec, km_paradero(bd, r07, cog) - km_antes, vel, ahora - timedelta(seconds=5))


if __name__ == "__main__":
    bd = ConexionBD()
    if "--si-vacia" in sys.argv and bd.consultar_uno("SELECT to_regclass('public.usuario') AS t")["t"] is not None:
        with bd.transaccion():
            bd.ejecutar(MODULO01.read_text(encoding="utf-8"))   # migración del Módulo 01 sobre una base existente
        print("La base ya tiene datos; no se vuelve a cargar (quite --si-vacia para reiniciarla).")
        sys.exit(0)
    with bd.transaccion():
        ids = sembrar(bd)
        if "--demo" in sys.argv:
            demo(bd, ids)
    print("Datos iniciales cargados:", {k: len(v) for k, v in ids.items()})
    print("Usuarios de prueba (contraseña", CLAVE + "):", ", ".join(u[1] for u in USUARIOS))
