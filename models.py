from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import db

# Modelo de Inscripción para relacionar Torneos y Equipos
class Inscripcion(db.Model):
    __tablename__ = "inscripciones"
    id = db.Column(db.Integer, primary_key=True)
    torneo_id = db.Column(db.Integer, db.ForeignKey("torneos.id"), nullable=False)
    equipo_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    torneo = db.relationship("Torneo", backref=db.backref("inscripciones_rel", lazy=True))
    equipo = db.relationship("Equipo", backref=db.backref("inscripciones_rel", lazy=True))

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
        secondary="inscripciones",
        backref=db.backref("torneos", lazy=True),
        overlaps="inscripciones_rel,torneo,equipo"
    )

class Equipo(db.Model):
    __tablename__ = "equipos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    categoria = db.Column(db.String(80)) # Juvenil, Libre, Femenil
    representante = db.Column(db.String(120))
    telefono = db.Column(db.String(30))
    logo_url = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Jugador(db.Model):
    __tablename__ = "jugadores"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellidos = db.Column(db.String(120), nullable=False)
    fecha_nacimiento = db.Column(db.Date)
    posicion = db.Column(db.String(50))
    equipo_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    
    equipo = db.relationship("Equipo", backref=db.backref("jugadores", lazy=True))

class Arbitro(db.Model):
    __tablename__ = "arbitros"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellidos = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30))
    activo = db.Column(db.Boolean, default=True, nullable=False)

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
    arbitro_id = db.Column(db.Integer, db.ForeignKey("arbitros.id"), nullable=True)

    fecha_hora = db.Column(db.DateTime, nullable=False)
    jornada = db.Column(db.String(50))
    estado = db.Column(db.String(30), default="programado")
    goles_local = db.Column(db.Integer, default=0)
    goles_visitante = db.Column(db.Integer, default=0)

    torneo = db.relationship("Torneo", backref=db.backref("partidos", lazy=True))
    cancha = db.relationship("Cancha", backref=db.backref("partidos", lazy=True))
    arbitro = db.relationship("Arbitro", backref=db.backref("partidos", lazy=True))
    local = db.relationship("Equipo", foreign_keys=[local_id])
    visitante = db.relationship("Equipo", foreign_keys=[visitante_id])

class Gol(db.Model):
    __tablename__ = "goles"
    id = db.Column(db.Integer, primary_key=True)
    partido_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), nullable=False)
    jugador_id = db.Column(db.Integer, db.ForeignKey("jugadores.id"), nullable=False)
    minuto = db.Column(db.Integer)
    tipo = db.Column(db.String(50), default="normal") # normal, penal, autogol

    partido = db.relationship("Partido", backref=db.backref("eventos_goles", lazy=True))
    jugador = db.relationship("Jugador", backref=db.backref("goles_anotados", lazy=True))

class Incidencia(db.Model):
    __tablename__ = "incidencias"
    id = db.Column(db.Integer, primary_key=True)
    partido_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), nullable=False)
    jugador_id = db.Column(db.Integer, db.ForeignKey("jugadores.id"), nullable=False)
    tipo = db.Column(db.String(50), nullable=False) # Amarilla, Roja, Lesion
    minuto = db.Column(db.Integer)
    descripcion = db.Column(db.String(255))

    partido = db.relationship("Partido", backref=db.backref("eventos_incidencias", lazy=True))
    jugador = db.relationship("Jugador", backref=db.backref("incidencias", lazy=True))

class Anuncio(db.Model):
    __tablename__ = "anuncios"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True, nullable=False)