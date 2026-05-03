from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import db

# =========================================================
# USUARIOS DEL SISTEMA
# =========================================================
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

# =========================================================
# ENTIDADES BASE 
# =========================================================
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

class Equipo(db.Model):
    __tablename__ = "equipos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    representante = db.Column(db.String(120))
    telefono = db.Column(db.String(30))
    logo_url = db.Column(db.String(255))
    categoria = db.Column(db.String(50))
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Cancha(db.Model):
    __tablename__ = "canchas"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    ubicacion = db.Column(db.String(150))
    tipo = db.Column(db.String(50))
    disponibilidad = db.Column(db.String(20), default="Disponible")

class Jugador(db.Model):
    __tablename__ = "jugadores"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    apellido_paterno = db.Column(db.String(60), nullable=False)
    apellido_materno = db.Column(db.String(60))
    fecha_nacimiento = db.Column(db.Date)
    sexo = db.Column(db.String(20))

class Arbitro(db.Model):
    __tablename__ = "arbitros"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    apellido_paterno = db.Column(db.String(60), nullable=False)
    apellido_materno = db.Column(db.String(60))
    telefono = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(35), default="Activo")

class Anuncio(db.Model):
    __tablename__ = "anuncios"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(20), default="Visible")

# =========================================================
# ENTIDADES DE RELACIÓN
# =========================================================
class Inscripcion(db.Model):
    __tablename__ = "inscripciones"
    id = db.Column(db.Integer, primary_key=True)
    torneo_id = db.Column(db.Integer, db.ForeignKey("torneos.id"), nullable=False)
    equipo_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=False)
    fecha_inscripcion = db.Column(db.Date, default=datetime.utcnow)
    estado_inscripcion = db.Column(db.String(35), default="Pagada")
    
    torneo = db.relationship("Torneo", backref="equipos_inscritos")
    equipo = db.relationship("Equipo", backref="mis_torneos")

class RegistroJugador(db.Model):
    __tablename__ = "registro_jugador"
    id = db.Column(db.Integer, primary_key=True)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey("inscripciones.id"), nullable=False)
    jugador_id = db.Column(db.Integer, db.ForeignKey("jugadores.id"), nullable=False)
    dorsal = db.Column(db.Integer, nullable=False)
    es_capitan = db.Column(db.Boolean, default=False)

    inscripcion = db.relationship("Inscripcion", backref="roster_jugadores")
    jugador = db.relationship("Jugador", backref="mis_registros")

class Partido(db.Model):
    __tablename__ = "partidos"
    id = db.Column(db.Integer, primary_key=True)
    torneo_id = db.Column(db.Integer, db.ForeignKey("torneos.id"), nullable=False)
    cancha_id = db.Column(db.Integer, db.ForeignKey("canchas.id"), nullable=True)
    arbitro_id = db.Column(db.Integer, db.ForeignKey("arbitros.id"), nullable=True)
    
    inscripcion_1_id = db.Column(db.Integer, db.ForeignKey("inscripciones.id"), nullable=False)
    inscripcion_2_id = db.Column(db.Integer, db.ForeignKey("inscripciones.id"), nullable=False)
    
    fecha_hora = db.Column(db.DateTime, nullable=False)
    jornada = db.Column(db.String(20))
    estado = db.Column(db.String(35), default="Programado")

    inscripcion_1 = db.relationship("Inscripcion", foreign_keys=[inscripcion_1_id])
    inscripcion_2 = db.relationship("Inscripcion", foreign_keys=[inscripcion_2_id])
    cancha = db.relationship("Cancha")
    arbitro = db.relationship("Arbitro")
    torneo = db.relationship("Torneo")

class Gol(db.Model):
    __tablename__ = "goles"
    id = db.Column(db.Integer, primary_key=True)
    partido_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), nullable=False)
    
   
    registro_jugador_id = db.Column(db.Integer, db.ForeignKey("registro_jugador.id"), nullable=True)
    
    partido = db.relationship("Partido", backref=db.backref("goles", lazy=True))

class Incidencia(db.Model):
    __tablename__ = "incidencias"
    id = db.Column(db.Integer, primary_key=True)
    partido_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), nullable=False)
    registro_jugador_id = db.Column(db.Integer, db.ForeignKey("registro_jugador.id"), nullable=False)
    tipo = db.Column(db.String(40), nullable=False) 
    descripcion = db.Column(db.String(255), nullable=False)


    # =========================================================
# CONTACTO DE EMERGENCIA
# =========================================================
class ContactoEmergencia(db.Model):
    __tablename__ = "contacto_emergencia"
    id = db.Column(db.Integer, primary_key=True)
    
    # Se conecta directo al jugador
    jugador_id = db.Column(db.Integer, db.ForeignKey("jugadores.id"), nullable=False)
    
    nombre_contacto = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    parentesco = db.Column(db.String(40), nullable=False)

    # uselist=False significa que es una relación 1 a 1 (un jugador = un contacto)
    jugador = db.relationship("Jugador", backref=db.backref("contacto_emergencia", uselist=False))

# =========================================================
# PAGOS (Inscripción y Arbitraje)
# =========================================================
class PagoInscripcion(db.Model):
    __tablename__ = "pago_inscripcion"
    id = db.Column(db.Integer, primary_key=True)
    
    # Se conecta a la inscripción
    inscripcion_id = db.Column(db.Integer, db.ForeignKey("inscripciones.id"), unique=True, nullable=False)
    
    fecha_pago = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(db.String(30), nullable=False)

    inscripcion = db.relationship("Inscripcion", backref=db.backref("pago", uselist=False))

class PagoArbitraje(db.Model):
    __tablename__ = "pago_arbitraje"
    id = db.Column(db.Integer, primary_key=True)
    
    # El pago de arbitraje se asocia a un partido y a una inscripción en específico
    partido_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), nullable=False)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey("inscripciones.id"), nullable=False)
    
    fecha_pago = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(db.String(30), nullable=False)

    partido = db.relationship("Partido", backref="pagos_arbitraje")
    inscripcion = db.relationship("Inscripcion", backref="pagos_arbitraje")




class LogActividad(db.Model):
    __tablename__ = "logs_actividad"
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    modulo = db.Column(db.String(50)) 
    movimiento = db.Column(db.String(100)) 
    responsable = db.Column(db.String(80)) 
    estatus = db.Column(db.String(20)) 