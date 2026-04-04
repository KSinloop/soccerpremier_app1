from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import db


inscripciones = db.Table(
    "inscripciones",
    db.Column("torneo_id", db.Integer, db.ForeignKey("torneos.id"), primary_key=True),
    db.Column("equipo_id", db.Integer, db.ForeignKey("equipos.id"), primary_key=True),
)


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Torneo(db.Model):
    __tablename__ = "torneos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(80))
    tipo = db.Column(db.String(50))
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    equipos = db.relationship(
        "Equipo",
        secondary=inscripciones,
        backref=db.backref("torneos", lazy=True)
    )


class Equipo(db.Model):
    __tablename__ = "equipos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    representante = db.Column(db.String(120))
    telefono = db.Column(db.String(30))
    logo_url = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Cancha(db.Model):
    __tablename__ = "canchas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    ubicacion = db.Column(db.String(150))
    tipo = db.Column(db.String(50))
    disponible = db.Column(db.Boolean, default=True, nullable=False)


class Partido(db.Model):
    __tablename__ = "partidos"

    id = db.Column(db.Integer, primary_key=True)
    torneo_id = db.Column(db.Integer, db.ForeignKey("torneos.id"), nullable=False)
    local_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=False)
    visitante_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=False)
    cancha_id = db.Column(db.Integer, db.ForeignKey("canchas.id"), nullable=True)

    fecha_hora = db.Column(db.DateTime, nullable=False)
    jornada = db.Column(db.String(50))
    estado = db.Column(db.String(30), default="programado")
    goles_local = db.Column(db.Integer, nullable=True)
    goles_visitante = db.Column(db.Integer, nullable=True)

    torneo = db.relationship("Torneo", backref=db.backref("partidos", lazy=True))
    cancha = db.relationship("Cancha", backref=db.backref("partidos", lazy=True))
    local = db.relationship("Equipo", foreign_keys=[local_id])
    visitante = db.relationship("Equipo", foreign_keys=[visitante_id])