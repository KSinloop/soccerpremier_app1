CREATE DATABASE IF NOT EXISTS soccerpremier;
USE soccerpremier;

-- =========================================================
-- TABLA: torneo
-- =========================================================
CREATE TABLE IF NOT EXISTS torneo (
    id_torneo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    division VARCHAR(50) NOT NULL,
    visibilidad VARCHAR(35) NOT NULL,
    estado VARCHAR(35) NOT NULL,
    tipo VARCHAR(30) NOT NULL
);

-- =========================================================
-- TABLA: equipo
-- =========================================================
CREATE TABLE IF NOT EXISTS equipo (
    id_equipo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    division VARCHAR(50) NOT NULL,
    estado VARCHAR(50) NOT NULL
);

-- =========================================================
-- TABLA: inscripcion
-- =========================================================
CREATE TABLE IF NOT EXISTS inscripcion (
    id_inscripcion INT AUTO_INCREMENT PRIMARY KEY,
    id_torneo INT NOT NULL,
    id_equipo INT NOT NULL,
    fecha_inscripcion DATE NOT NULL,
    estado_inscripcion VARCHAR(35) NOT NULL,

    CONSTRAINT fk_inscripcion_torneo
        FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),

    CONSTRAINT fk_inscripcion_equipo
        FOREIGN KEY (id_equipo) REFERENCES equipo(id_equipo),

    CONSTRAINT uq_inscripcion_torneo_equipo
        UNIQUE (id_torneo, id_equipo)
);

-- =========================================================
-- TABLA: jugador
-- =========================================================
CREATE TABLE IF NOT EXISTS jugador (
    id_jugador INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL,
    apellido_paterno VARCHAR(60) NOT NULL,
    apellido_materno VARCHAR(60),
    fecha_nacimiento DATE NOT NULL,
    sexo VARCHAR(20) NOT NULL
);

-- =========================================================
-- TABLA: registro_jugador
-- =========================================================
CREATE TABLE IF NOT EXISTS registro_jugador (
    id_registro_jugador INT AUTO_INCREMENT PRIMARY KEY,
    id_inscripcion INT NOT NULL,
    id_jugador INT NOT NULL,
    dorsal INT NOT NULL,
    es_capitan BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_registro_jugador_inscripcion
        FOREIGN KEY (id_inscripcion) REFERENCES inscripcion(id_inscripcion),

    CONSTRAINT fk_registro_jugador_jugador
        FOREIGN KEY (id_jugador) REFERENCES jugador(id_jugador),

    CONSTRAINT uq_registro_inscripcion_jugador
        UNIQUE (id_inscripcion, id_jugador),

    CONSTRAINT uq_registro_inscripcion_dorsal
        UNIQUE (id_inscripcion, dorsal)
);

-- =========================================================
-- TABLA: contacto_emergencia
-- =========================================================
CREATE TABLE IF NOT EXISTS contacto_emergencia (
    id_contacto_emergencia INT AUTO_INCREMENT PRIMARY KEY,
    id_jugador INT NOT NULL,
    nombre_contacto VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    parentesco VARCHAR(40) NOT NULL,

    CONSTRAINT fk_contacto_emergencia_jugador
        FOREIGN KEY (id_jugador) REFERENCES jugador(id_jugador)
);

-- =========================================================
-- TABLA: cancha
-- =========================================================
CREATE TABLE IF NOT EXISTS cancha (
    id_cancha INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    estado VARCHAR(35) NOT NULL
);

-- =========================================================
-- TABLA: arbitro
-- =========================================================
CREATE TABLE IF NOT EXISTS arbitro (
    id_arbitro INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL,
    apellido_paterno VARCHAR(60) NOT NULL,
    apellido_materno VARCHAR(60),
    telefono VARCHAR(20) NOT NULL,
    estado VARCHAR(35) NOT NULL
);

-- =========================================================
-- TABLA: partido
-- =========================================================
CREATE TABLE IF NOT EXISTS partido (
    id_partido INT AUTO_INCREMENT PRIMARY KEY,
    id_torneo INT NOT NULL,
    id_cancha INT NOT NULL,
    id_arbitro INT NOT NULL,
    id_inscripcion_1 INT NOT NULL,
    id_inscripcion_2 INT NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    estado VARCHAR(35) NOT NULL,

    CONSTRAINT fk_partido_torneo
        FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),

    CONSTRAINT fk_partido_cancha
        FOREIGN KEY (id_cancha) REFERENCES cancha(id_cancha),

    CONSTRAINT fk_partido_arbitro
        FOREIGN KEY (id_arbitro) REFERENCES arbitro(id_arbitro),

    CONSTRAINT fk_partido_inscripcion_1
        FOREIGN KEY (id_inscripcion_1) REFERENCES inscripcion(id_inscripcion),

    CONSTRAINT fk_partido_inscripcion_2
        FOREIGN KEY (id_inscripcion_2) REFERENCES inscripcion(id_inscripcion),

    CONSTRAINT chk_partido_inscripciones_distintas
        CHECK (id_inscripcion_1 <> id_inscripcion_2)
);

-- =========================================================
-- TABLA: pago_inscripcion
-- Relación 1:1 con inscripcion
-- =========================================================
CREATE TABLE IF NOT EXISTS pago_inscripcion (
    id_pago_inscripcion INT AUTO_INCREMENT PRIMARY KEY,
    id_inscripcion INT NOT NULL,
    fecha_pago DATE NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    metodo_pago VARCHAR(30) NOT NULL,

    CONSTRAINT fk_pago_inscripcion_inscripcion
        FOREIGN KEY (id_inscripcion) REFERENCES inscripcion(id_inscripcion),

    CONSTRAINT uq_pago_inscripcion_id_inscripcion
        UNIQUE (id_inscripcion)
);

-- =========================================================
-- TABLA: pago_arbitraje
-- =========================================================
CREATE TABLE IF NOT EXISTS pago_arbitraje (
    id_pago_arbitraje INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT NOT NULL,
    id_inscripcion INT NOT NULL,
    fecha_pago DATE NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    metodo_pago VARCHAR(30) NOT NULL,

    CONSTRAINT fk_pago_arbitraje_partido
        FOREIGN KEY (id_partido) REFERENCES partido(id_partido),

    CONSTRAINT fk_pago_arbitraje_inscripcion
        FOREIGN KEY (id_inscripcion) REFERENCES inscripcion(id_inscripcion)
);

-- =========================================================
-- TABLA: incidencia
-- =========================================================
CREATE TABLE IF NOT EXISTS incidencia (
    id_incidencia INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT NOT NULL,
    id_registro_jugador INT NOT NULL,
    id_inscripcion INT NOT NULL,
    tipo VARCHAR(40) NOT NULL,
    descripcion VARCHAR(255) NOT NULL,

    CONSTRAINT fk_incidencia_partido
        FOREIGN KEY (id_partido) REFERENCES partido(id_partido),

    CONSTRAINT fk_incidencia_registro_jugador
        FOREIGN KEY (id_registro_jugador) REFERENCES registro_jugador(id_registro_jugador),

    CONSTRAINT fk_incidencia_inscripcion
        FOREIGN KEY (id_inscripcion) REFERENCES inscripcion(id_inscripcion)
);

-- =========================================================
-- TABLA: gol
-- =========================================================
CREATE TABLE IF NOT EXISTS gol (
    id_gol INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT NOT NULL,
    id_registro_jugador INT NOT NULL,
    id_inscripcion INT NOT NULL,

    CONSTRAINT fk_gol_partido
        FOREIGN KEY (id_partido) REFERENCES partido(id_partido),

    CONSTRAINT fk_gol_registro_jugador
        FOREIGN KEY (id_registro_jugador) REFERENCES registro_jugador(id_registro_jugador),

    CONSTRAINT fk_gol_inscripcion
        FOREIGN KEY (id_inscripcion) REFERENCES inscripcion(id_inscripcion)
);

USE soccerpremier;

CREATE TABLE IF NOT EXISTS usuario_admin (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL,
    rol VARCHAR(30) NOT NULL DEFAULT 'admin',
    estado VARCHAR(20) NOT NULL DEFAULT 'activo'
);

USE soccerpremier;

ALTER TABLE equipo
ADD COLUMN nombre_dt VARCHAR(100) NOT NULL AFTER nombre;
