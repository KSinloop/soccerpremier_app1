USE soccerpremier;

-- TORNEO
INSERT INTO torneo (nombre, categoria, division, visibilidad, estado, tipo)
VALUES ('Apertura 2026', 'Juvenil', 'Primera', 'Publico', 'Activo', 'Liga');

-- EQUIPOS
INSERT INTO equipo (nombre, categoria, division, estado)
VALUES 
('Halcones FC', 'Juvenil', 'Primera', 'Activo'),
('Leones FC', 'Juvenil', 'Primera', 'Activo');

-- JUGADORES
INSERT INTO jugador (nombre, apellido_paterno, apellido_materno, fecha_nacimiento, sexo)
VALUES
('Juan', 'Perez', 'Lopez', '2008-05-10', 'Masculino'),
('Luis', 'Martinez', 'Garcia', '2008-07-21', 'Masculino'),
('Carlos', 'Ramirez', 'Santos', '2007-11-03', 'Masculino');

-- CANCHA
INSERT INTO cancha (nombre, estado)
VALUES ('Cancha 1', 'Disponible');

-- ARBITRO
INSERT INTO arbitro (nombre, apellido_paterno, apellido_materno, telefono, estado)
VALUES ('Mario', 'Lopez', 'Diaz', '8123456789', 'Activo');

-- INSCRIPCIONES
INSERT INTO inscripcion (id_torneo, id_equipo, fecha_inscripcion, estado_inscripcion)
VALUES
(1, 1, '2026-04-04', 'Pagada'),
(1, 2, '2026-04-04', 'Pagada');

-- REGISTRO JUGADOR
INSERT INTO registro_jugador (id_inscripcion, id_jugador, dorsal, es_capitan)
VALUES
(1, 1, 10, TRUE),
(1, 2, 7, FALSE),
(2, 3, 9, TRUE);

-- PARTIDO
INSERT INTO partido (id_torneo, id_cancha, id_arbitro, id_inscripcion_1, id_inscripcion_2, fecha, hora, estado)
VALUES
(1, 1, 1, 1, 2, '2026-04-10', '18:00:00', 'Programado');

-- PAGO INSCRIPCION
INSERT INTO pago_inscripcion (id_inscripcion, fecha_pago, monto, metodo_pago)
VALUES
(1, '2026-04-04', 1500.00, 'Transferencia'),
(2, '2026-04-04', 1500.00, 'Efectivo');

-- PAGO ARBITRAJE
INSERT INTO pago_arbitraje (id_partido, id_inscripcion, fecha_pago, monto, metodo_pago)
VALUES
(1, 1, '2026-04-09', 300.00, 'Transferencia'),
(1, 2, '2026-04-09', 300.00, 'Efectivo');

-- GOLES
INSERT INTO gol (id_partido, id_registro_jugador, id_inscripcion)
VALUES
(1, 1, 1),
(1, 3, 2);

-- INCIDENCIAS
INSERT INTO incidencia (id_partido, id_registro_jugador, id_inscripcion, tipo, descripcion)
VALUES
(1, 2, 1, 'Tarjeta Amarilla', 'Falta por juego brusco');