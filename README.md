# BusCerca

Aplicación para conocer en tiempo real la ubicación y la llegada del transporte público rural.
Repositorio del proyecto de Análisis de Sistemas, Universidad Distrital Francisco José de Caldas.

Equipo: Faiber Ariza, Samuel Rodríguez y Karol Balderrama.

| Módulo | Sprint | Contenido |
|---|---|---|
| 02 Panel del Conductor | 2 | Iniciar recorrido, transmitir GPS cada 10 s (también sin conexión), velocidad promedio, novedades y finalizar |
| 03 Panel del Pasajero | 3 | Buscar rutas por destino, bus en el mapa, ficha del vehículo, tiempo de llegada al paradero y favoritos |

## Estructura (tres capas)

```
backend/            API REST en Python + FastAPI (capa lógica)
  app/api/          servicios REST (rutas HTTP)
  app/control/      clases de control del modelo de análisis (ControlRecorrido, ControlLlegada, ...)
  app/entidades/    clases entidad (Ruta, Recorrido, Ubicacion, Favorito, ...)
  app/datos/        ConexionBD: único acceso a PostgreSQL
  tests/            casos de prueba automatizados (CP-0201-01 ... CP-0305-05)
  seed.py           crea el esquema y carga los datos iniciales
  simulador.py      simula el celular de un conductor para la demostración
database/           script de la base de datos (PostgreSQL 16 + PostGIS)
app-android/        aplicación Android en Kotlin (capa de presentación)
docs/               documento del parcial y guía del equipo
```

## Sin instalar nada: Render + GitHub Actions

1. **API y base de datos en Render:** en render.com, *New > Blueprint*, elegir este repositorio y aplicar.
   `render.yaml` crea la base PostgreSQL y la API, carga los datos de prueba y deja dos buses moviéndose solos
   (`SIMULAR_BUSES=1`). La API queda en `https://buscerca-api.onrender.com` (o el nombre que asigne Render);
   en el plan gratuito se duerme tras 15 minutos sin uso y tarda cerca de 1 minuto en despertar.
2. **APK en GitHub Actions:** en el repositorio, *Settings > Secrets and variables > Actions > Variables*,
   crear `API_URL` con la dirección de Render. En *Actions > APK Android > Run workflow* se compila la app;
   el APK se descarga desde el resultado de la ejecución (*Artifacts > BusCerca-apk*) y se instala en el celular.
3. **Pruebas:** *Actions > Pruebas API* ejecuta los 44 casos con PostgreSQL + PostGIS en cada cambio.

## 1. Base de datos

Requisitos: PostgreSQL 16 con la extensión PostGIS.

```sql
CREATE USER buscerca WITH PASSWORD 'buscerca';
CREATE DATABASE buscerca_db OWNER buscerca;
CREATE DATABASE buscerca_test OWNER buscerca;   -- para las pruebas
-- en cada base, como superusuario:  CREATE EXTENSION postgis;
```

## 2. API (backend)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py --demo                                   # esquema + datos iniciales + 2 buses en curso
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

La documentación interactiva de la API queda en `http://localhost:8000/docs`.
Para ver un bus moviéndose en el mapa: `python simulador.py` (en otra terminal).

### Pruebas

```bash
python -m pytest -v            # 44 casos: tests/test_sprint2.py y tests/test_sprint3.py
```

## 3. Aplicación Android

1. Abrir la carpeta `app-android` en Android Studio (Koala o más reciente) y esperar la sincronización de Gradle.
2. En `app/build.gradle.kts`, `API_URL` apunta a `http://10.0.2.2:8000/` (el computador visto desde el emulador).
   En un celular real, escribir la IP del computador en el enlace **Servidor** de la pantalla de inicio de sesión
   (celular y computador en la misma red WiFi).
3. Ejecutar en un emulador o celular con Android 8.0 o superior. Para generar el APK: *Build > Build APK(s)*.
4. Pruebas unitarias de la lógica de la app: `./gradlew testDebugUnitTest`.

## Usuarios de prueba

Contraseña de todos: `BusCerca2026*`

| Rol | Correo |
|---|---|
| Conductor (bus 014, Jorge Ramírez) | jorge.ramirez@buscerca.co |
| Conductor | luis.pardo@buscerca.co, martha.rojas@buscerca.co |
| Pasajero | pasajera@buscerca.co, pasajero2@buscerca.co |
| Administrador (Módulo 05) | admin@buscerca.co |

Para la demostración del pasajero, buscar **Rodamontal**: aparecen las rutas R-07 y R-11 con abordaje en Cogua centro.
