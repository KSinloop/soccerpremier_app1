from flask import Blueprint, jsonify, request, render_template
from db import db
from models import Torneo, Equipo, Cancha, Partido, Anuncio, Jugador, Inscripcion, RegistroJugador, Gol, Incidencia
from sqlalchemy import func

public_bp = Blueprint("public", __name__)


# -----------------------------
# VISTAS HTML
# -----------------------------
@public_bp.get("/")
def index():
    torneos_db = db.session.execute(
        db.select(Torneo).order_by(Torneo.id.desc())
    ).scalars().all()

    equipos_db = db.session.execute(
        db.select(Equipo).order_by(Equipo.nombre.asc())
    ).scalars().all()

    torneo_id = request.args.get("torneo_id", type=int)

    stmt = db.select(Partido).order_by(Partido.fecha_hora.asc())
    if torneo_id:
        stmt = stmt.filter_by(torneo_id=torneo_id)

    partidos_db = db.session.execute(stmt).scalars().all()

    canchas_db = db.session.execute(
        db.select(Cancha).order_by(Cancha.id.desc())
    ).scalars().all()

    anuncios_db = db.session.execute(
        db.select(Anuncio).where(Anuncio.estado == "Visible")
    ).scalars().all()
    return render_template("public/index.html", torneos = torneos_db, equipos = equipos_db, partidos = partidos_db, canchas = canchas_db, anuncios = anuncios_db)

@public_bp.get("/torneos")
def pagina_torneos():
    filtro_actual = request.args.get("filtro", "Todos")
    
    if filtro_actual == "Activos":
        active = 1
    else:
        active = 0

    if filtro_actual == "Todos":
        torneos_db = db.session.execute(db.select(Torneo).order_by(Torneo.activo)).scalars().all()
    else:
        torneos_db = db.session.execute(db.select(Torneo).where(Torneo.activo == active)).scalars().all()

    return render_template("public/torneos.html", torneos = torneos_db, filtro_actual = filtro_actual)

@public_bp.get("/equipos")
def pagina_equipos():
    equipos_db = db.session.execute(
        db.select(Equipo).order_by(Equipo.nombre.asc())
    ).scalars().all()
    return render_template("public/equipos.html", equipos = equipos_db)

@public_bp.get("/partidos")
def pagina_partidos():
    torneo_id = request.args.get("torneo_id", type=int)

    stmt = db.select(Partido).order_by(Partido.fecha_hora.asc())
    if torneo_id:
        stmt = stmt.filter_by(torneo_id=torneo_id)

    partidos_db = db.session.execute(stmt).scalars().all()
    return render_template("public/partidos.html", partidos = partidos_db)

def calcular_marcador(partido):
    insc1_id = partido.inscripcion_1_id
    insc2_id = partido.inscripcion_2_id

    goles_1 = 0
    goles_2 = 0
    for gol in partido.goles:
        # El gol tiene registro_jugador_id → ese RegistroJugador tiene inscripcion_id
        if gol.registro_jugador_id:
            reg = db.session.get(RegistroJugador, gol.registro_jugador_id)
            if reg:
                if reg.inscripcion_id == insc1_id:
                    goles_1 += 1
                elif reg.inscripcion_id == insc2_id:
                    goles_2 += 1
    return goles_1, goles_2

@public_bp.get("/resultados")
def pagina_resultados():
    partidos = db.session.execute(
        db.select(Partido).where(Partido.estado == "Finalizado")
    ).scalars().all()

    resultados_db = []
    for p in partidos:
        g1, g2 = calcular_marcador(p)
        resultados_db.append({
            "partido": p,
            "goles_1": g1,
            "goles_2": g2
        })

    return render_template("public/resultados.html", resultados = resultados_db)

@public_bp.get("/posiciones")
def pagina_posiciones():
    torneos = db.session.execute(db.select(Torneo).order_by(Torneo.id.desc())).scalars().all()
    torneo_id = request.args.get("torneo_id", type=int)

    # Si no mandan torneo_id, usamos el primero disponible
    if not torneo_id and torneos:
        torneo_id = torneos[0].id

    tabla = []

    if torneo_id:
        partidos = db.session.execute(
            db.select(Partido)
            .where(Partido.torneo_id == torneo_id)
            .where(Partido.estado == "Finalizado")
        ).scalars().all()

        # Inicializamos stats por inscripcion
        stats = {}
        for partido in partidos:
            for insc in [partido.inscripcion_1, partido.inscripcion_2]:
                if insc.id not in stats:
                    stats[insc.id] = {
                        "nombre": insc.equipo.nombre,
                        "PJ": 0, "G": 0, "E": 0, "P": 0,
                        "GF": 0, "GC": 0
                    }

        # Procesamos cada partido
        for partido in partidos:
            g1, g2 = calcular_marcador(partido)
            id1 = partido.inscripcion_1_id
            id2 = partido.inscripcion_2_id

            # Goles
            stats[id1]["GF"] += g1
            stats[id1]["GC"] += g2
            stats[id2]["GF"] += g2
            stats[id2]["GC"] += g1

            # Partidos jugados
            stats[id1]["PJ"] += 1
            stats[id2]["PJ"] += 1

            # Resultado
            if g1 > g2:
                stats[id1]["G"] += 1
                stats[id2]["P"] += 1
            elif g1 == g2:
                stats[id1]["E"] += 1
                stats[id2]["E"] += 1
            else:
                stats[id2]["G"] += 1
                stats[id1]["P"] += 1

        # Calculamos DG y PTS, convertimos a lista
        for s in stats.values():
            s["DG"] = s["GF"] - s["GC"]
            s["PTS"] = s["G"] * 3 + s["E"]

        # Ordenamos: primero por puntos, luego por DG como desempate
        tabla = sorted(stats.values(), key=lambda x: (x["PTS"], x["DG"]), reverse=True)

    return render_template(
        "public/posiciones.html",
        tabla=tabla,
        torneos=torneos,
        torneo_id=torneo_id
    )

@public_bp.get("/estadisticas")
def pagina_estadisticas():
    total_goles = db.session.scalar(db.select(func.count(Gol.id))) or 0
    total_amarillas = db.session.scalar(db.select(func.count(Incidencia.id)).where(Incidencia.tipo == "Tarjeta Amarilla")) or 0
    total_rojas = db.session.scalar(db.select(func.count(Incidencia.id)).where(Incidencia.tipo == "Tarjeta Roja")) or 0

    top_goleadores_query = (
        db.select(
            Jugador.nombre,
            Jugador.apellido_paterno,
            Equipo.nombre.label('equipo_nombre'),
            func.count(Gol.id).label('total_goles')
        )
        .select_from(Gol)
        .join(RegistroJugador, Gol.registro_jugador_id == RegistroJugador.id)
        .join(Jugador, RegistroJugador.jugador_id == Jugador.id)
        .join(Inscripcion, RegistroJugador.inscripcion_id == Inscripcion.id)
        .join(Equipo, Inscripcion.equipo_id == Equipo.id)
        .group_by(Jugador.id, Equipo.id)
        .order_by(func.count(Gol.id).desc())
        .limit(10)
    )

    top_amonestados_query = (
        db.select(
            Jugador.nombre,
            Jugador.apellido_paterno,
            Equipo.nombre.label('equipo_nombre'),
            func.sum(
                db.case((Incidencia.tipo == "Tarjeta Amarilla", 1), else_=0)
            ).label('amarillas'),
            func.sum(
                db.case((Incidencia.tipo == "Tarjeta Roja", 1), else_=0)
            ).label('rojas'),
            func.count(Incidencia.id).label('total_tarjetas')
        )
        .select_from(Incidencia)
        .join(RegistroJugador, Incidencia.registro_jugador_id == RegistroJugador.id)
        .join(Jugador, RegistroJugador.jugador_id == Jugador.id)
        .join(Inscripcion, RegistroJugador.inscripcion_id == Inscripcion.id)
        .join(Equipo, Inscripcion.equipo_id == Equipo.id)
        .where(Incidencia.tipo.in_(["Tarjeta Amarilla", "Tarjeta Roja"]))
        .group_by(Jugador.id, Equipo.id)
        .order_by(func.count(Incidencia.id).desc())
        .limit(10)
    )

    top_amonestados = db.session.execute(top_amonestados_query).all()
    top_goleadores = db.session.execute(top_goleadores_query).all()

    return render_template(
        "public/estadisticas.html", 
        total_goles=total_goles,
        total_amarillas=total_amarillas,
        total_rojas=total_rojas,
        top_goleadores=top_goleadores,
        top_amonestados=top_amonestados
    )

@public_bp.get("/canchas")
def pagina_canchas():
    filtro_actual = request.args.get("filtro", "Todas")

    if filtro_actual == "Todas":
        canchas_db = db.session.execute(db.select(Cancha).order_by(Cancha.id.desc())).scalars().all()
    else:
        canchas_db = db.session.execute(db.select(Cancha).where(Cancha.disponibilidad == filtro_actual)).scalars().all()

    return render_template("public/canchas.html", canchas = canchas_db, filtro_actual = filtro_actual)

@public_bp.get("/anuncios")
def pagina_anuncios():
    anuncios_db = db.session.execute(
        db.select(Anuncio).where(Anuncio.estado == "Visible")
    ).scalars().all()
    return render_template("public/anuncios.html", anuncios = anuncios_db)

@public_bp.get("/login")
def pagina_login():
    return render_template("public/login.html")


# -----------------------------
# API
# -----------------------------
@public_bp.get("/health")
def health():
    return jsonify({
        "ok": True,
        "servicio": "soccerpremier_backend"
    })


@public_bp.get("/api/torneos")
def listar_torneos():
    torneos = db.session.execute(
        db.select(Torneo).order_by(Torneo.id.desc())
    ).scalars().all()

    return jsonify([
        {
            "id": t.id,
            "nombre": t.nombre,
            "categoria": t.categoria,
            "tipo": t.tipo,
            "fecha_inicio": t.fecha_inicio.isoformat() if t.fecha_inicio else None,
            "fecha_fin": t.fecha_fin.isoformat() if t.fecha_fin else None,
            "activo": t.activo
        }
        for t in torneos
    ])


@public_bp.get("/api/equipos")
def listar_equipos():
    equipos = db.session.execute(
        db.select(Equipo).order_by(Equipo.nombre.asc())
    ).scalars().all()

    return jsonify([
        {
            "id": e.id,
            "nombre": e.nombre,
            "representante": e.representante,
            "telefono": e.telefono,
            "logo_url": e.logo_url,
            "categoria": e.categoria,
            "activo": e.activo
        }
        for e in equipos
    ])

@public_bp.get("/api/anuncios")
def listar_anuncios():
    anuncios = db.session.execute(
        db.select(Anuncio).order_by(Anuncio.id.desc())
    ).scalars().all()

    return jsonify([
        {
            "id": a.id,
            "titulo": a.titulo,
            "contenido": a.contenido,
            "fecha": a.fecha_publicacion,
            "estado": a.estado
        }
        for a in anuncios
    ])

@public_bp.get("/api/partidos")
def listar_partidos():
    torneo_id = request.args.get("torneo_id", type=int)

    stmt = db.select(Partido).order_by(Partido.fecha_hora.asc())
    if torneo_id:
        stmt = stmt.filter_by(torneo_id=torneo_id)

    partidos = db.session.execute(stmt).scalars().all()

    return jsonify([
        {
            "id": p.id,
            "torneo_id": p.torneo_id,
            "torneo": p.torneo.nombre,
            "local": p.inscripcion_1.equipo.nombre,
            "visitante": p.inscripcion_2.equipo.nombre,
            "cancha": p.cancha.nombre if p.cancha else None,
            "fecha_hora": p.fecha_hora.isoformat(),
            "jornada": p.jornada,
            "estado": p.estado,
            "goles_local": len(p.goles), # provisional
            "goles_visitante": 0 # provisional
        }
        for p in partidos
    ])