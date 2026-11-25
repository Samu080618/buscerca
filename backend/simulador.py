"""Simula el celular de un conductor para la demostración: inicia (o retoma) su recorrido y envía una
coordenada cada 10 segundos avanzando sobre el trazado de la ruta, como lo hace ServicioGPS.

Uso: python simulador.py --api http://localhost:8000 --correo jorge.ramirez@buscerca.co --ruta R-07 --vehiculo 014
"""
import argparse
import math
import time
from datetime import datetime

import httpx

CLAVE = "BusCerca2026*"


def distancia_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def punto_en(trazado, km):
    for a, b in zip(trazado, trazado[1:]):
        d = distancia_km(a, b)
        if km <= d:
            f = km / d
            return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        km -= d
    return trazado[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--correo", default="jorge.ramirez@buscerca.co")
    ap.add_argument("--ruta", default="R-07")
    ap.add_argument("--vehiculo", default="014")
    ap.add_argument("--velocidad", type=float, default=32.0, help="km/h")
    ap.add_argument("--intervalo", type=float, default=10.0, help="segundos entre coordenadas")
    a = ap.parse_args()
    c = httpx.Client(base_url=a.api, timeout=10)
    tok = c.post("/api/auth/login", json={"correo": a.correo, "contrasena": CLAVE}).json()["token"]
    c.headers["Authorization"] = f"Bearer {tok}"
    act = c.get("/api/recorridos/activo")
    if act.status_code == 200:
        rec = act.json()
    else:
        op = c.get("/api/recorridos/opciones").json()
        ruta = next(r for r in op["rutas"] if r["codigo"] == a.ruta)
        veh = next(v for v in op["vehiculos"] if v["numero_interno"] == a.vehiculo)
        rec = c.post("/api/recorridos", json={"id_ruta": ruta["id_ruta"], "id_vehiculo": veh["id_vehiculo"]}).json()
    traz = c.get(f"/api/rutas/{rec['ruta']['id']}/trazado").json()["trazado"]
    total = sum(distancia_km(x, y) for x, y in zip(traz, traz[1:]))
    km = 0.0
    print(f"Recorrido {rec['id_recorrido']} en {rec['ruta']['codigo']} ({total:.1f} km). Ctrl+C para detener.")
    while km <= total:
        lat, lon = punto_en(traz, km)
        r = c.post(f"/api/recorridos/{rec['id_recorrido']}/ubicaciones",
                   json={"coordenadas": [{"latitud": round(lat, 6), "longitud": round(lon, 6), "velocidad": a.velocidad,
                                          "fecha_hora": datetime.now().replace(microsecond=0).isoformat()}]})
        print(f"{datetime.now():%H:%M:%S} km {km:5.2f}  {r.status_code} {r.json()}")
        if r.status_code != 201:
            break
        km += a.velocidad * a.intervalo / 3600
        time.sleep(a.intervalo)
    c.patch(f"/api/recorridos/{rec['id_recorrido']}/finalizar")


if __name__ == "__main__":
    main()
