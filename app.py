import click
from flask import Flask
from config import Config
from db import db, login_manager
from models import Admin
from routes.public import public_bp
from routes.auth import auth_bp
from routes.admin import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Admin, int(user_id))

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        click.echo("Base de datos inicializada correctamente.")

    @app.cli.command("crear-admin")
    @click.argument("username")
    @click.argument("password")
    def crear_admin(username, password):
        existente = db.session.execute(
            db.select(Admin).filter_by(username=username)
        ).scalar_one_or_none()

        if existente:
            click.echo("Ese administrador ya existe.")
            return

        admin = Admin(username=username)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        click.echo(f"Administrador '{username}' creado correctamente.")

    return app


app = create_app()