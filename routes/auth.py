from flask import Blueprint, jsonify, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from db import db
from models import Admin

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    # detectar si es JSON o form data
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"ok": False, "error": "Debes enviar username y password"}), 400

    admin = db.session.execute(
        db.select(Admin).filter_by(username=username, activo=True)
    ).scalar_one_or_none()

    if not admin or not admin.check_password(password):
        # Si la contraseña es incorrecta, regresar a login
        flash("Credenciales inválidas")
        return redirect(url_for('public.pagina_login'))

    login_user(admin)

    #mandar directo al dasjboard del admin
    return redirect(url_for('admin.vista_dashboard'))

@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.index'))

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