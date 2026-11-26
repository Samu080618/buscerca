-- BusCerca — Módulo 01 (Autenticación y Perfiles): recuperación de contraseña y cierre de sesión seguro.
-- Se puede ejecutar varias veces (IF NOT EXISTS); seed.py lo aplica también sobre una base existente.
CREATE TABLE IF NOT EXISTS recuperacion_contrasena (
  id_recuperacion  SERIAL PRIMARY KEY,
  id_usuario       INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
  codigo_hash      VARCHAR(100) NOT NULL,
  expira           TIMESTAMP NOT NULL,
  intentos         INTEGER NOT NULL DEFAULT 0,
  usado            BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS token_revocado (
  jti     VARCHAR(40) PRIMARY KEY,
  expira  TIMESTAMP NOT NULL
);
