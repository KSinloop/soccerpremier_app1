USE soccerpremier;

SELECT * FROM torneo;
SELECT * FROM equipo;
SELECT * FROM jugador;
SELECT * FROM inscripcion;
SELECT * FROM registro_jugador;
SELECT * FROM partido;
SELECT * FROM gol;
SELECT * FROM incidencia;

SELECT 
    i.id_inscripcion,
    t.nombre AS torneo,
    e.nombre AS equipo,
    i.fecha_inscripcion,
    i.estado_inscripcion
FROM inscripcion i
INNER JOIN torneo t ON i.id_torneo = t.id_torneo
INNER JOIN equipo e ON i.id_equipo = e.id_equipo;