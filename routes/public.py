from flask import Blueprint, jsonify, request, render_template
from db import db
from models import Torneo, Equipo, Partido

public_bp = Blueprint("public", __name__)


# -----------------------------
# VISTAS HTML
# -----------------------------
@public_bp.get("/")
def index():
    return render_template("public/index.html")

@public_bp.get("/torneos")
def pagina_torneos():
    return render_template("public/torneos.html")

@public_bp.get("/equipos")
def pagina_equipos():
    return render_template("public/equipos.html")

@public_bp.get("/partidos")
def pagina_partidos():
    return render_template("public/partidos.html")

@public_bp.get("/resultados")
def pagina_resultados():
    return render_template("public/resultados.html")

@public_bp.get("/posiciones")
def pagina_posiciones():
    return render_template("public/posiciones.html")

@public_bp.get("/estadisticas")
def pagina_estadisticas():
    return render_template("public/estadisticas.html")

@public_bp.get("/canchas")
def pagina_canchas():
    return render_template("public/canchas.html")

@public_bp.get("/anuncios")
def pagina_anuncios():
    return render_template("public/anuncios.html")

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
            "activo": e.activo
        }
        for e in equipos
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
            "local": p.local.nombre,
            "visitante": p.visitante.nombre,
            "cancha": p.cancha.nombre if p.cancha else None,
            "fecha_hora": p.fecha_hora.isoformat(),
            "jornada": p.jornada,
            "estado": p.estado,
            "goles_local": p.goles_local,
            "goles_visitante": p.goles_visitante
        }
        for p in partidos
    ])