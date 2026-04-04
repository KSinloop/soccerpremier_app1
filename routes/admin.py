from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from db import db
from models import Torneo, Equipo, Cancha, Partido

admin_bp = Blueprint("admin", __name__)

# -----------------------------
# VISTAS HTML ADMIN
# -----------------------------
@admin_bp.get("/")
def dashboard():
    return render_template("admin/dashboard.html")

@admin_bp.get("/login")
def login_admin():
    return render_template("admin/login_admin.html")

@admin_bp.get("/torneos")
def vista_torneos_admin():
    return render_template("admin/torneos_admin.html")

@admin_bp.get("/equipos")
def vista_equipos_admin():
    return render_template("admin/equipos_admin.html")

@admin_bp.get("/partidos")
def vista_partidos_admin():
    return render_template("admin/partidos_admin.html")

@admin_bp.get("/canchas")
def vista_canchas_admin():
    return render_template("admin/canchas_admin.html")

@admin_bp.get("/estadisticas")
def vista_estadisticas_admin():
    return render_template("admin/estadisticas_admin.html")

@admin_bp.get("/anuncios")
def vista_anuncios_admin():
    return render_template("admin/anuncios_admin.html")


# -----------------------------
# API ADMIN
# -----------------------------
@admin_bp.post("/torneos")
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
        fecha_fin=datetime.strptime(data["fecha_fin"], "%Y-%m-%d").date() if data.get("fecha_fin") else None,
        activo=data.get("activo", True)
    )

    db.session.add(torneo)
    db.session.commit()

    return jsonify({"ok": True, "id": torneo.id, "mensaje": "Torneo creado"}), 201