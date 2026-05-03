from flask import Blueprint, jsonify, request, render_template
from db import db
from models import Torneo, Equipo, Partido, Anuncio, Cancha

public_bp = Blueprint("public", __name__)


# -----------------------------
# VISTAS HTML
# -----------------------------
@public_bp.get("/")
def index():
    return render_template("public/index.html")

@public_bp.get("/torneos")
def pagina_torneos():
    torneos_db = db.session.execute(
        db.select(Torneo).order_by(Torneo.id.desc())
    ).scalars().all()
    return render_template("public/torneos.html", torneos = torneos_db)

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

@public_bp.get("/resultados")
def pagina_resultados():
    resultados_db = db.session.execute(
        db.select(Partido).where(Partido.estado == "Finalizado")
    ).scalars().all()
    return render_template("public/resultados.html", resultados = resultados_db)

@public_bp.get("/posiciones")
def pagina_posiciones():
    return render_template("public/posiciones.html")

@public_bp.get("/estadisticas")
def pagina_estadisticas():
    return render_template("public/estadisticas.html")

@public_bp.get("/canchas")
def pagina_canchas():
    canchas_db = db.session.execute(
        db.select(Cancha).order_by(Cancha.id.desc())
    ).scalars().all()
    return render_template("public/canchas.html", canchas = canchas_db)

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