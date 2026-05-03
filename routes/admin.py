from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from db import db
from models import Torneo, Equipo, Cancha, Partido, Jugador, Arbitro, Anuncio, Gol, Incidencia, Inscripcion

admin_bp = Blueprint("admin", __name__)

# -----------------------------
# VISTAS HTML ADMIN
# -----------------------------
@admin_bp.get("/")
@login_required
def dashboard():
    stats = {
        "torneos": Torneo.query.count(),
        "equipos": Equipo.query.count(),
        "partidos": Partido.query.count(),
        "anuncios": Anuncio.query.count()
    }
    return render_template("admin/dashboard.html", stats=stats)

@admin_bp.get("/login")
def login_admin():
    return render_template("admin/login_admin.html")

@admin_bp.get("/torneos")
@login_required
def vista_torneos_admin():
    torneos = Torneo.query.all()
    return render_template("admin/torneos_admin.html", torneos=torneos)

@admin_bp.get("/equipos")
@login_required
def vista_equipos_admin():
    equipos = Equipo.query.all()
    return render_template("admin/equipos_admin.html", equipos=equipos)

@admin_bp.get("/jugadores")
@login_required
def vista_jugadores_admin():
    jugadores = Jugador.query.all()
    equipos = Equipo.query.all()
    return render_template("admin/jugadores_admin.html", jugadores=jugadores, equipos=equipos)

@admin_bp.get("/partidos")
@login_required
def vista_partidos_admin():
    partidos = Partido.query.all()
    torneos = Torneo.query.all()
    equipos = Equipo.query.all()
    canchas = Cancha.query.all()
    arbitros = Arbitro.query.all()
    return render_template("admin/partidos_admin.html", partidos=partidos, torneos=torneos, equipos=equipos, canchas=canchas, arbitros=arbitros)

@admin_bp.get("/canchas")
@login_required
def vista_canchas_admin():
    canchas = Cancha.query.all()
    return render_template("admin/canchas_admin.html", canchas=canchas)

@admin_bp.get("/arbitros")
@login_required
def vista_arbitros_admin():
    arbitros = Arbitro.query.all()
    return render_template("admin/arbitros_admin.html", arbitros=arbitros)

@admin_bp.get("/anuncios")
@login_required
def vista_anuncios_admin():
    anuncios = Anuncio.query.order_by(Anuncio.fecha_publicacion.desc()).all()
    return render_template("admin/anuncios_admin.html", anuncios=anuncios)

# -----------------------------
# API ADMIN (CRUD)
# -----------------------------

# TORNEOS
@admin_bp.post("/api/torneos")
@login_required
def crear_torneo():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre", "").strip()
    if not nombre:
        return jsonify({"ok": False, "error": "El nombre es obligatorio"}), 400

    torneo = Torneo(
        nombre=nombre,
        categoria=data.get("categoria"),
        tipo=data.get("tipo"),
        fecha_inicio=datetime.strptime(data["fecha_inicio"], "%Y-%m-%d").date() if data.get("fecha_inicio") else None,
        fecha_fin=datetime.strptime(data["fecha_fin"], "%Y-%m-%d").date() if data.get("fecha_fin") else None
    )
    db.session.add(torneo)
    db.session.commit()
    return jsonify({"ok": True, "mensaje": "Torneo creado"}), 201

# EQUIPOS
@admin_bp.post("/api/equipos")
@login_required
def crear_equipo():
    data = request.get_json()
    equipo = Equipo(
        nombre=data.get("nombre"),
        representante=data.get("representante"),
        telefono=data.get("telefono"),
        categoria=data.get("categoria", "Libre")
    )
    db.session.add(equipo)
    db.session.commit()
    return jsonify({"ok": True, "mensaje": "Equipo creado"}), 201

# JUGADORES
@admin_bp.post("/api/jugadores")
@login_required
def crear_jugador():
    data = request.get_json()
    jugador = Jugador(
        nombre=data.get("nombre"),
        apellidos=data.get("apellidos"),
        posicion=data.get("posicion"),
        equipo_id=data.get("equipo_id"),
        fecha_nacimiento=datetime.strptime(data["fecha_nacimiento"], "%Y-%m-%d").date() if data.get("fecha_nacimiento") else None
    )
    db.session.add(jugador)
    db.session.commit()
    return jsonify({"ok": True, "mensaje": "Jugador registrado"}), 201

# PARTIDOS
@admin_bp.post("/api/partidos")
@login_required
def crear_partido():
    data = request.get_json()
    partido = Partido(
        torneo_id=data.get("torneo_id"),
        local_id=data.get("local_id"),
        visitante_id=data.get("visitante_id"),
        cancha_id=data.get("cancha_id"),
        arbitro_id=data.get("arbitro_id"),
        fecha_hora=datetime.strptime(data["fecha_hora"], "%Y-%m-%dT%H:%M"),
        jornada=data.get("jornada")
    )
    db.session.add(partido)
    db.session.commit()
    return jsonify({"ok": True, "mensaje": "Partido programado"}), 201

# RESULTADOS
@admin_bp.post("/api/partidos/<int:partido_id>/resultado")
@login_required
def registrar_resultado(partido_id):
    data = request.get_json()
    partido = Partido.query.get_or_404(partido_id)
    partido.goles_local = data.get("goles_local", 0)
    partido.goles_visitante = data.get("goles_visitante", 0)
    partido.estado = "finalizado"
    db.session.commit()
    return jsonify({"ok": True, "mensaje": "Resultado registrado"}), 200

# CANCHAS
@admin_bp.post("/api/canchas")
@login_required
def crear_cancha():
    data = request.get_json()
    cancha = Cancha(
        nombre=data.get("nombre"),
        ubicacion=data.get("ubicacion"),
        tipo=data.get("tipo", "Fútbol")
    )
    db.session.add(cancha)
    db.session.commit()
    return jsonify({"ok": True, "mensaje": "Cancha registrada"}), 201

# ARBITROS
@admin_bp.post("/api/arbitros")
@login_required
def crear_arbitro():
    data = request.get_json()
    arbitro = Arbitro(
        nombre=data.get("nombre"),
        apellidos=data.get("apellidos"),
        telefono=data.get("telefono")
    )
    db.session.add(arbitro)
    db.session.commit()
    return jsonify({"ok": True, "mensaje": "Árbitro registrado"}), 201

# ANUNCIOS
@admin_bp.post("/api/anuncios")
@login_required
def crear_anuncio():
    data = request.get_json()
    anuncio = Anuncio(
        titulo=data.get("titulo"),
        contenido=data.get("contenido")
    )
    db.session.add(anuncio)
    db.session.commit()
    return jsonify({"ok": True, "mensaje": "Anuncio publicado"}), 201

# --- API ADICIONAL (BORRAR / EDITAR) ---

@admin_bp.delete("/api/<string:modelo>/<int:id>")
@login_required
def eliminar_registro(modelo, id):
    model_map = {
        "torneos": Torneo, "equipos": Equipo, "jugadores": Jugador,
        "partidos": Partido, "canchas": Cancha, "arbitros": Arbitro, "anuncios": Anuncio
    }
    if modelo not in model_map: return jsonify({"ok": False, "error": "No válido"}), 400
    obj = model_map[modelo].query.get(id)
    if not obj: return jsonify({"ok": False, "error": "No encontrado"}), 404
    db.session.delete(obj)
    db.session.commit()
    return jsonify({"ok": True})

@admin_bp.put("/api/equipos/<int:id>")
@login_required
def editar_equipo_api(id):
    equipo = Equipo.query.get_or_404(id)
    data = request.get_json()
    equipo.nombre = data.get("nombre", equipo.nombre)
    equipo.representante = data.get("representante", equipo.representante)
    equipo.categoria = data.get("categoria", equipo.categoria)
    equipo.telefono = data.get("telefono", equipo.telefono)
    db.session.commit()
    return jsonify({"ok": True})