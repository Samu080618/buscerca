-- BusCerca — esquema de la base de datos (PostgreSQL 16 + PostGIS)
-- Módulo 01 (usuario), Módulo 02 (Sprint 2) y Módulo 03 (Sprint 3)
CREATE EXTENSION IF NOT EXISTS postgis;

DROP TABLE IF EXISTS recuperacion_contrasena, token_revocado, favorito, novedad, tipo_novedad, ubicacion, recorrido, estado_recorrido,
  ruta_paradero, paradero, vehiculo, ruta, usuario CASCADE;

-- Módulo 01 (con foto_url agregada en el Sprint 3)
CREATE TABLE usuario (
  id_usuario      SERIAL PRIMARY KEY,
  nombre          VARCHAR(80)  NOT NULL,
  correo          VARCHAR(120) NOT NULL UNIQUE,
  contrasena_hash VARCHAR(100) NOT NULL,
  rol             VARCHAR(20)  NOT NULL CHECK (rol IN ('CONDUCTOR', 'PASAJERO', 'ADMINISTRADOR')),
  documento       VARCHAR(20),
  telefono        VARCHAR(20),
  direccion       VARCHAR(120),
  foto_url        VARCHAR(200),
  activo          BOOLEAN NOT NULL DEFAULT TRUE
);

-- Sprint 2 (ruta y vehiculo ampliadas en el Sprint 3)
CREATE TABLE ruta (
  id_ruta                  SERIAL PRIMARY KEY,
  codigo                   VARCHAR(10)  NOT NULL UNIQUE,
  nombre                   VARCHAR(60)  NOT NULL,
  origen                   VARCHAR(60)  NOT NULL,
  destino                  VARCHAR(60)  NOT NULL,
  trazado                  GEOGRAPHY(LINESTRING, 4326),
  velocidad_historica_kmh  NUMERIC(5,2) NOT NULL DEFAULT 25 CHECK (velocidad_historica_kmh > 0),
  estado                   VARCHAR(10)  NOT NULL DEFAULT 'Activa' CHECK (estado IN ('Activa', 'Inactiva'))
);

CREATE TABLE vehiculo (
  id_vehiculo     SERIAL PRIMARY KEY,
  placa           VARCHAR(6)  NOT NULL UNIQUE,
  numero_interno  VARCHAR(10) NOT NULL,
  tipo            VARCHAR(15) NOT NULL DEFAULT 'Bus' CHECK (tipo IN ('Bus', 'Colectivo', 'Escalera')),
  empresa         VARCHAR(80) NOT NULL DEFAULT 'Cooperativa veredal'
);

CREATE TABLE estado_recorrido (
  id_estado    INTEGER PRIMARY KEY,
  descripcion  VARCHAR(20) NOT NULL UNIQUE
);
INSERT INTO estado_recorrido VALUES (1, 'EN CURSO'), (2, 'FINALIZADO'), (3, 'PROGRAMADO'), (4, 'CANCELADO');

CREATE TABLE recorrido (
  id_recorrido  SERIAL PRIMARY KEY,
  id_usuario    INTEGER NOT NULL REFERENCES usuario(id_usuario),
  id_vehiculo   INTEGER NOT NULL REFERENCES vehiculo(id_vehiculo),
  id_ruta       INTEGER NOT NULL REFERENCES ruta(id_ruta),
  id_estado     INTEGER NOT NULL REFERENCES estado_recorrido(id_estado),
  fecha_inicio  TIMESTAMP NOT NULL,
  fecha_fin     TIMESTAMP,
  CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);
-- RN-201: un conductor solo puede tener un recorrido EN CURSO
CREATE UNIQUE INDEX ux_recorrido_en_curso ON recorrido (id_usuario) WHERE id_estado = 1;

CREATE TABLE ubicacion (
  id_ubicacion        BIGSERIAL PRIMARY KEY,
  id_recorrido        INTEGER NOT NULL REFERENCES recorrido(id_recorrido) ON DELETE CASCADE,
  latitud             NUMERIC(9,6) NOT NULL CHECK (latitud BETWEEN -90 AND 90),
  longitud            NUMERIC(9,6) NOT NULL CHECK (longitud BETWEEN -180 AND 180),
  posicion            GEOGRAPHY(POINT, 4326) NOT NULL,
  velocidad           NUMERIC(5,2),
  velocidad_promedio  NUMERIC(5,2),
  km_en_ruta          NUMERIC(6,2),
  fecha_hora          TIMESTAMP NOT NULL,
  UNIQUE (id_recorrido, fecha_hora)          -- RN-204: sin duplicados
);
CREATE INDEX ix_ubicacion_recorrido_fecha ON ubicacion (id_recorrido, fecha_hora DESC);

CREATE TABLE tipo_novedad (
  id_tipo_novedad  SERIAL PRIMARY KEY,
  descripcion      VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE novedad (
  id_novedad       SERIAL PRIMARY KEY,
  id_recorrido     INTEGER NOT NULL REFERENCES recorrido(id_recorrido) ON DELETE CASCADE,
  id_tipo_novedad  INTEGER NOT NULL REFERENCES tipo_novedad(id_tipo_novedad),
  comentario       VARCHAR(200),
  latitud          NUMERIC(9,6),
  longitud         NUMERIC(9,6),
  fecha_hora       TIMESTAMP NOT NULL
);

-- Sprint 3
CREATE TABLE paradero (
  id_paradero          SERIAL PRIMARY KEY,
  nombre               VARCHAR(80) NOT NULL,
  nombre_normalizado   VARCHAR(80) NOT NULL,   -- RN-301: búsqueda sin tildes ni mayúsculas
  vereda               VARCHAR(60),
  municipio            VARCHAR(60) NOT NULL,
  latitud              NUMERIC(9,6) NOT NULL,
  longitud             NUMERIC(9,6) NOT NULL,
  posicion             GEOGRAPHY(POINT, 4326) NOT NULL,
  oficial              BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX ix_paradero_nombre ON paradero (nombre_normalizado);
CREATE INDEX ix_paradero_posicion ON paradero USING GIST (posicion);

CREATE TABLE ruta_paradero (
  id_ruta          INTEGER NOT NULL REFERENCES ruta(id_ruta) ON DELETE CASCADE,
  id_paradero      INTEGER NOT NULL REFERENCES paradero(id_paradero) ON DELETE CASCADE,
  orden            INTEGER NOT NULL CHECK (orden > 0),
  km_desde_inicio  NUMERIC(6,2) NOT NULL CHECK (km_desde_inicio >= 0),
  PRIMARY KEY (id_ruta, id_paradero),
  UNIQUE (id_ruta, orden)
);

CREATE TABLE favorito (
  id_favorito     SERIAL PRIMARY KEY,
  id_pasajero     INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
  tipo            VARCHAR(10) NOT NULL CHECK (tipo IN ('RUTA', 'PARADERO')),
  id_ruta         INTEGER REFERENCES ruta(id_ruta) ON DELETE CASCADE,
  id_paradero     INTEGER REFERENCES paradero(id_paradero) ON DELETE CASCADE,
  alias           VARCHAR(30),
  fecha_creacion  TIMESTAMP NOT NULL DEFAULT now(),
  CHECK ((tipo = 'RUTA' AND id_ruta IS NOT NULL) OR (tipo = 'PARADERO' AND id_paradero IS NOT NULL))
);
-- RN-310: sin repetidos por pasajero, ruta y paradero
CREATE UNIQUE INDEX ux_favorito ON favorito (id_pasajero, tipo, COALESCE(id_ruta, 0), COALESCE(id_paradero, 0));
