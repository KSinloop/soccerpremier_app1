from flask import Blueprint, jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from db import db
from models import Admin

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"ok": False, "error": "Debes enviar username y password"}), 400

    admin = db.session.execute(
        db.select(Admin).filter_by(username=username, activo=True)
    ).scalar_one_or_none()

    if not admin or not admin.check_password(password):
        return jsonify({"ok": False, "error": "Credenciales inválidas"}), 401

    login_user(admin)

    return jsonify({
        "ok": True,
        "mensaje": "Sesión iniciada",
        "admin": {
            "id": admin.id,
            "username": admin.username
        }
    })


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True, "mensaje": "Sesión cerrada"})


@auth_bp.get("/me")
def me():
    if current_user.is_authenticated:
        return jsonify({
            "autenticado": True,
            "admin": {
                "id": current_user.id,
                "username": current_user.username
            }
        })

    return jsonify({"autenticado": False})