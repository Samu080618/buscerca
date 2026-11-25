"""Modo demostración (variable SIMULAR_BUSES=1): mueve solos los buses de prueba sobre su ruta cada 10 s,
para sustentar sin tener que ejecutar simulador.py. No toca los recorridos que inicie un conductor desde la app."""
import threading
import time

from app import reloj
from app.datos.conexion_bd import ConexionBD

CORREOS_DEMO = ("jorge.ramirez@buscerca.co", "martha.rojas@buscerca.co")
INTERVALO = 10


def _paso(bd: ConexionBD):
    filas = bd.consultar(
        """SELECT r.id_recorrido, ST_Length(ru.trazado) / 1000 AS largo,
                  (SELECT u.km_en_ruta FROM ubicacion u WHERE u.id_recorrido = r.id_recorrido ORDER BY u.fecha_hora DESC LIMIT 1) AS km
           FROM recorrido r JOIN usuario us USING (id_usuario) JOIN ruta ru USING (id_ruta)
           WHERE r.id_estado = 1 AND us.correo = ANY(%s)""", (list(CORREOS_DEMO),))
    for f in filas:
        vel = 30.0
        km = float(f["km"] or 0) + vel * INTERVALO / 3600
        if km > float(f["largo"]) - 0.05:   # al llegar al final vuelve a empezar la ruta
            km = 0.0
        bd.ejecutar(
            """INSERT INTO ubicacion (id_recorrido, latitud, longitud, posicion, velocidad, velocidad_promedio, km_en_ruta, fecha_hora)
               SELECT r.id_recorrido, round(ST_Y(pt)::numeric, 6), round(ST_X(pt)::numeric, 6), pt::geography, %(v)s, %(v)s, %(km)s, %(f)s
               FROM recorrido r JOIN ruta ru USING (id_ruta),
                    LATERAL (SELECT ST_LineInterpolatePoint(ru.trazado::geometry, LEAST(1, %(km)s * 1000 / ST_Length(ru.trazado))) AS pt) x
               WHERE r.id_recorrido = %(r)s
               ON CONFLICT (id_recorrido, fecha_hora) DO NOTHING""",
            {"r": f["id_recorrido"], "km": round(km, 2), "v": vel, "f": reloj.ahora()})
    bd.confirmar()


def _ciclo():
    while True:
        bd = ConexionBD()
        try:
            _paso(bd)
        except Exception as e:  # la demostración nunca debe tumbar la API
            print("simulador de demostración:", e)
            bd.deshacer()
        finally:
            bd.cerrar()
        time.sleep(INTERVALO)


def iniciar():
    threading.Thread(target=_ciclo, daemon=True, name="simulador-demo").start()
