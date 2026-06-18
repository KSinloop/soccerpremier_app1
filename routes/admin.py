import os
from werkzeug.utils import secure_filename
from datetime import datetime, date as date_type, timedelta
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from db import db
from models import Torneo, Equipo, Cancha, Partido, Anuncio, Jugador, Inscripcion, RegistroJugador, ContactoEmergencia, Arbitro, Gol, Incidencia, LogMovimiento, PagoArbitraje, BloqueHorario
from sqlalchemy import func

COSTO_ARBITRAJE = 150.00

admin_bp = Blueprint("admin", __name__)

def registrar_movimiento(modulo, movimiento, estatus="Completado"):
    """Función rápida para guardar logs en la base de datos"""
    
    # Sacamos el 'username' del administrador conectado
    if current_user.is_authenticated:
        nombre_admin = current_user.username 
    else:
        nombre_admin = "Sistema" 

    nuevo_log = LogMovimiento(
        modulo=modulo,
        movimiento=movimiento,
        responsable=nombre_admin,
        estatus=estatus
    )
    db.session.add(nuevo_log)
    db.session.commit()

# -----------------------------
# VISTAS HTML ADMIN
# -----------------------------
@admin_bp.get("/")
@admin_bp.route("/dashboard") 
def vista_dashboard():
    torneos_activos = len(db.session.execute(db.select(Torneo).where(Torneo.activo==True)).scalars().all())
    equipos_registrados = len(db.session.execute(db.select(Equipo)).scalars().all())
    partidos_programados = len(db.session.execute(db.select(Partido).where(Partido.estado=='Programado')).scalars().all())
    anuncios_activos = len(db.session.execute(db.select(Anuncio)).scalars().all())
    
    movimientos_recientes = db.session.execute(
        db.select(LogMovimiento).order_by(LogMovimiento.fecha.desc()).limit(7)
    ).scalars().all()

    return render_template("admin/dashboard.html", 
                           tot_torneos=torneos_activos, 
                           tot_equipos=equipos_registrados, 
                           tot_partidos=partidos_programados, 
                           tot_anuncios=anuncios_activos,
                           movimientos_recientes=movimientos_recientes)

@admin_bp.get("/login")
def login_admin():
    return render_template("admin/login_admin.html")

@admin_bp.get("/torneos")
def vista_torneos_admin():
    filtro = request.args.get("filtro", "Todos")
    
    if filtro == "Activos":
        torneos_db = db.session.execute(db.select(Torneo).where(Torneo.estado == "Activo")).scalars().all()
    elif filtro == "Próximos":
        torneos_db = db.session.execute(db.select(Torneo).where(Torneo.estado == "Próximo")).scalars().all()
    elif filtro == "Finalizados":
        torneos_db = db.session.execute(db.select(Torneo).where(Torneo.estado == "Finalizado")).scalars().all()
    elif filtro == "Cancelados":
        torneos_db = db.session.execute(db.select(Torneo).where(Torneo.estado == "Cancelado")).scalars().all()
    else:
        torneos_db = db.session.execute(db.select(Torneo)).scalars().all()

    return render_template("admin/torneos_admin.html", torneos=torneos_db, filtro_actual=filtro)

@admin_bp.get("/equipos")
def vista_equipos_admin(): 
    categoria_actual = request.args.get("categoria", "Todos")
    if categoria_actual == "Todos":
        equipos = db.session.execute(db.select(Equipo)).scalars().all()
    else:
        equipos = db.session.execute(db.select(Equipo).where(Equipo.categoria == categoria_actual)).scalars().all()

    equipos_activos_query = db.session.execute(db.select(Equipo).where(Equipo.activo == True)).scalars().all()
    total_activos = len(equipos_activos_query)

    return render_template("admin/equipos_admin.html", 
                           equipos=equipos, 
                           categoria_actual=categoria_actual, 
                           total_activos=total_activos)

@admin_bp.get("/partidos")
def vista_partidos_admin():
    partidos_db = db.session.execute(db.select(Partido)).scalars().all()
    return render_template("admin/partidos_admin.html", partidos=partidos_db)

@admin_bp.get("/canchas")
def vista_canchas_admin():
    canchas_db = db.session.execute(db.select(Cancha)).scalars().all()
    return render_template("admin/canchas_admin.html", canchas=canchas_db)

@admin_bp.get("/estadisticas")
def vista_estadisticas_admin():
    # 1. Total Goles (Solo Fase Regular)
    total_goles = db.session.scalar(
        db.select(func.count(Gol.id))
        .join(Partido, Gol.partido_id == Partido.id)
        .where(Partido.tipo_partido == "Fase Regular")
    ) or 0

    # 2. Total Amarillas (Solo Fase Regular)
    total_amarillas = db.session.scalar(
        db.select(func.count(Incidencia.id))
        .join(Partido, Incidencia.partido_id == Partido.id)
        .where(Incidencia.tipo == "Tarjeta Amarilla")
        .where(Partido.tipo_partido == "Fase Regular")
    ) or 0

    # 3. Total Rojas (Solo Fase Regular)
    total_rojas = db.session.scalar(
        db.select(func.count(Incidencia.id))
        .join(Partido, Incidencia.partido_id == Partido.id)
        .where(Incidencia.tipo == "Tarjeta Roja")
        .where(Partido.tipo_partido == "Fase Regular")
    ) or 0

    # 4. Top Goleadores (Solo Fase Regular)
    top_goleadores_query = (
        db.select(
            Jugador.nombre,
            Jugador.apellido_paterno,
            Equipo.nombre.label('equipo_nombre'),
            func.count(Gol.id).label('total_goles')
        )
        .select_from(Gol)
        .join(Partido, Gol.partido_id == Partido.id) # <-- Conectamos con el partido
        .join(RegistroJugador, Gol.registro_jugador_id == RegistroJugador.id)
        .join(Jugador, RegistroJugador.jugador_id == Jugador.id)
        .join(Inscripcion, RegistroJugador.inscripcion_id == Inscripcion.id)
        .join(Equipo, Inscripcion.equipo_id == Equipo.id)
        .where(Partido.tipo_partido == "Fase Regular") # <-- Filtro de blindaje
        .group_by(Jugador.id, Equipo.id)
        .order_by(func.count(Gol.id).desc())
        .limit(5)
    )
    top_goleadores = db.session.execute(top_goleadores_query).all()

    return render_template(
        "admin/estadisticas_admin.html", 
        total_goles=total_goles,
        total_amarillas=total_amarillas,
        total_rojas=total_rojas,
        top_goleadores=top_goleadores
    )

@admin_bp.get("/anuncios")
def vista_anuncios_admin():
    anuncios_db = db.session.execute(db.select(Anuncio)).scalars().all()
    return render_template("admin/anuncios_admin.html", anuncios=anuncios_db)

# -----------------------------
# OPERACIONES CRUD (CREAR, EDITAR, ELIMINAR)
# -----------------------------

@admin_bp.route("/canchas/nueva", methods=["GET", "POST"])
def crear_cancha():
    if request.method == "POST":
        nueva_cancha = Cancha(
            nombre=request.form.get("nombre"), 
            ubicacion=request.form.get("ubicacion"), 
            tipo=request.form.get("tipo"), 
            disponibilidad="Disponible" 
        )
        db.session.add(nueva_cancha)
        db.session.commit()
        registrar_movimiento('Canchas', f'Alta de cancha: {nueva_cancha.nombre}')
        flash("¡Cancha agregada exitosamente!")
        return redirect(url_for('admin.vista_canchas_admin'))
    return render_template("admin/form_cancha.html")

@admin_bp.route("/anuncios/nuevo", methods=["GET", "POST"])
def crear_anuncio():
    if request.method == "POST":
        nuevo_anuncio = Anuncio(
            titulo=request.form.get("titulo"), 
            contenido=request.form.get("contenido"),
            categoria=request.form.get('categoria'),
            fecha_publicacion=datetime.strptime(request.form['fecha_publicacion'], '%Y-%m-%d').date(),  
        )
        db.session.add(nuevo_anuncio)
        db.session.commit()
        registrar_movimiento('Anuncios', f'Alta de anuncio: {nuevo_anuncio.titulo}')
        return redirect(url_for('admin.vista_anuncios_admin'))
    return render_template("admin/form_anuncio.html")

@admin_bp.route("/torneos/nuevo", methods=["GET", "POST"])
def crear_torneo():
    if request.method == "POST":
        f_ini = datetime.strptime(request.form.get("fecha_inicio"), "%Y-%m-%d").date() if request.form.get("fecha_inicio") else None
        f_fin = datetime.strptime(request.form.get("fecha_fin"), "%Y-%m-%d").date() if request.form.get("fecha_fin") else None

        nuevo_torneo = Torneo(
            nombre=request.form.get("nombre"),
            dia_torneo=request.form.get("dia_torneo"),
            categoria=request.form.get("categoria"),
            tipo=request.form.get("tipo"),
            estado=request.form.get("estado", "Próximo"),
            fecha_inicio=f_ini,
            fecha_fin=f_fin,
            activo=True
        )
        db.session.add(nuevo_torneo)
        db.session.commit()
        registrar_movimiento('Torneos', f'Alta de torneo: {nuevo_torneo.nombre}')
        return redirect(url_for('admin.vista_torneos_admin'))
    return render_template("admin/form_torneo.html")

@admin_bp.route("/equipos/nuevo", methods=["GET", "POST"])
def crear_equipo():
    if request.method == "POST":
        capitan_id_raw = request.form.get("capitan_id")
        nuevo_equipo = Equipo(
            nombre=request.form.get("nombre"),
            representante_nombre=request.form.get("representante_nombre"),
            representante_apellido=request.form.get("representante_apellido"),
            telefono=request.form.get("telefono"),
            categoria=request.form.get("categoria"),
            color_uniforme=request.form.get("color_uniforme"),
            capitan_id=int(capitan_id_raw) if capitan_id_raw else None,
            activo=True
        )
        db.session.add(nuevo_equipo)
        db.session.commit()
        registrar_movimiento('Equipos', f'Alta de equipo: {nuevo_equipo.nombre}')
        return redirect(url_for('admin.vista_equipos_admin'))
    jugadores = db.session.execute(db.select(Jugador)).scalars().all()
    return render_template("admin/form_equipo.html", jugadores=jugadores)

@admin_bp.route("/partidos/nuevo", methods=["GET", "POST"])
def crear_partido():
    if request.method == "POST":
        torneo_id = request.form.get("torneo_id")
        inscripcion_1_id = request.form.get("inscripcion_1_id")
        inscripcion_2_id = request.form.get("inscripcion_2_id")

        if inscripcion_1_id == inscripcion_2_id:
            flash("Error: Un equipo no puede jugar contra sí mismo. Selecciona equipos diferentes.", "error")
            return redirect(url_for('admin.crear_partido'))
        
        cancha_id = request.form.get("cancha_id")
        fecha_hora_str = request.form.get("fecha_hora")
        jornada = request.form.get("jornada")
        
        # NUEVO: Tipo de partido para separar Liguilla y Amistosos
        tipo_partido = request.form.get("tipo_partido", "Fase Regular")
        
        fecha_hora_obj = datetime.strptime(fecha_hora_str, "%Y-%m-%dT%H:%M")

        nuevo_partido = Partido( 
            torneo_id=torneo_id,
            inscripcion_1_id=inscripcion_1_id,
            inscripcion_2_id=inscripcion_2_id,
            cancha_id=cancha_id,
            fecha_hora=fecha_hora_obj,
            jornada=request.form.get("jornada"),
            tipo_partido=tipo_partido, 
            estado="Programado",
            arbitro_id=request.form.get("arbitro_id") if request.form.get("arbitro_id") else None
        )
        db.session.add(nuevo_partido)
        db.session.commit()
        registrar_movimiento('Partidos', f'Partido programado ID: {nuevo_partido.id}')

        pago_arb_1 = PagoArbitraje(
            partido_id=nuevo_partido.id,
            inscripcion_id=int(inscripcion_1_id),
            fecha_pago=date_type.today(),
            monto=COSTO_ARBITRAJE,
            metodo_pago="Pendiente"
        )
        pago_arb_2 = PagoArbitraje(
            partido_id=nuevo_partido.id,
            inscripcion_id=int(inscripcion_2_id),
            fecha_pago=date_type.today(),
            monto=COSTO_ARBITRAJE,
            metodo_pago="Pendiente"
        )
        db.session.add(pago_arb_1)
        db.session.add(pago_arb_2)
        db.session.commit()
        registrar_movimiento('Adeudos', f'Arbitraje generado para partido ID {nuevo_partido.id}')
        return redirect(url_for('admin.vista_partidos_admin'))

    torneos = db.session.execute(db.select(Torneo).where(Torneo.activo==True)).scalars().all()
    canchas = db.session.execute(db.select(Cancha)).scalars().all()
    inscripciones = db.session.execute(db.select(Inscripcion)).scalars().all()
    arbitros = db.session.execute(db.select(Arbitro).where(Arbitro.estado == "Activo")).scalars().all()

    return render_template("admin/form_partido.html", torneos=torneos, canchas=canchas, inscripciones=inscripciones, arbitros=arbitros)


# ==========================================
# editar eliminar canchas
# ==========================================
@admin_bp.route("/canchas/editar/<int:id>", methods=["GET", "POST"])
def editar_cancha(id):
    cancha = db.session.get(Cancha, id)
    if request.method == "POST":
        cancha.nombre = request.form.get("nombre")
        cancha.ubicacion = request.form.get("ubicacion")
        cancha.tipo = request.form.get("tipo")
        cancha.disponibilidad = request.form.get("disponibilidad")
        db.session.commit()
        registrar_movimiento('Canchas', f'Se editó la cancha: {cancha.nombre}')
        return redirect(url_for('admin.vista_canchas_admin'))
    return render_template("admin/editar_cancha.html", cancha=cancha)

@admin_bp.route("/canchas/eliminar/<int:id>")
def eliminar_cancha(id):
    cancha = db.session.get(Cancha, id)
    if cancha:
        nombre_cancha = cancha.nombre
        db.session.delete(cancha)
        db.session.commit()
        registrar_movimiento('Canchas', f'Se eliminó la cancha: {nombre_cancha}')
    return redirect(url_for('admin.vista_canchas_admin'))

@admin_bp.route("/torneos/editar/<int:id>", methods=["GET", "POST"])
def editar_torneo(id):
    torneo = db.session.get(Torneo, id)
    if request.method == "POST":
        torneo.nombre = request.form.get("nombre")
        torneo.dia_torneo = request.form.get("dia_torneo")
        torneo.categoria = request.form.get("categoria")
        torneo.tipo = request.form.get("tipo")
        torneo.estado = request.form.get("estado")
        f_ini = request.form.get("fecha_inicio")
        f_fin = request.form.get("fecha_fin")
        torneo.fecha_inicio = datetime.strptime(f_ini, "%Y-%m-%d").date() if f_ini else None
        torneo.fecha_fin = datetime.strptime(f_fin, "%Y-%m-%d").date() if f_fin else None
        db.session.commit()
        registrar_movimiento('Torneos', f'Se editó el torneo: {torneo.nombre}')
        return redirect(url_for('admin.vista_torneos_admin'))
    return render_template("admin/editar_torneo.html", torneo=torneo)

@admin_bp.route("/torneos/eliminar/<int:id>")
def eliminar_torneo(id):
    torneo = db.session.get(Torneo, id)
    if torneo:
        nombre_torneo = torneo.nombre
        db.session.delete(torneo)
        db.session.commit()
        registrar_movimiento('Torneos', f'Se eliminó el torneo: {nombre_torneo}')
    return redirect(url_for('admin.vista_torneos_admin'))

@admin_bp.route("/equipos/editar/<int:id>", methods=["GET", "POST"])
def editar_equipo(id):
    equipo = db.session.get(Equipo, id)
    if request.method == "POST":
        equipo.nombre = request.form.get("nombre")
        equipo.representante_nombre = request.form.get("representante_nombre")
        equipo.representante_apellido = request.form.get("representante_apellido")
        equipo.telefono = request.form.get("telefono")
        equipo.categoria = request.form.get("categoria")
        equipo.color_uniforme = request.form.get("color_uniforme")
        capitan_id_raw = request.form.get("capitan_id")
        equipo.capitan_id = int(capitan_id_raw) if capitan_id_raw else None
        db.session.commit()
        registrar_movimiento('Equipos', f'Se editó el equipo: {equipo.nombre}')
        return redirect(url_for('admin.vista_equipos_admin'))
    jugadores = db.session.execute(db.select(Jugador)).scalars().all()
    return render_template("admin/editar_equipo.html", equipo=equipo, jugadores=jugadores)

@admin_bp.route("/equipos/eliminar/<int:id>")
def eliminar_equipo(id):
    equipo = db.session.get(Equipo, id)
    if equipo:
        nombre_eq = equipo.nombre
        db.session.delete(equipo)
        db.session.commit()
        registrar_movimiento('Equipos', f'Se eliminó el equipo: {nombre_eq}')
    return redirect(url_for('admin.vista_equipos_admin'))

@admin_bp.route("/anuncios/editar/<int:id>", methods=["GET", "POST"])
def editar_anuncio(id):
    anuncio = db.session.get(Anuncio, id)
    if request.method == "POST":
        anuncio.titulo = request.form.get("titulo")
        anuncio.contenido = request.form.get("contenido")
        anuncio.categoria = request.form.get("categoria")
        anuncio.fecha_publicacion=datetime.strptime(request.form['fecha_publicacion'], '%Y-%m-%d').date()
        db.session.commit()
        registrar_movimiento('Anuncios', f'Se editó el anuncio: {anuncio.titulo}')
        return redirect(url_for('admin.vista_anuncios_admin'))
    return render_template("admin/editar_anuncio.html", anuncio=anuncio)

@admin_bp.route("/anuncios/eliminar/<int:id>")
def eliminar_anuncio(id):
    anuncio = db.session.get(Anuncio, id)
    if anuncio:
        titulo_an = anuncio.titulo
        db.session.delete(anuncio)
        db.session.commit()
        registrar_movimiento('Anuncios', f'Se eliminó el anuncio: {titulo_an}')
    return redirect(url_for('admin.vista_anuncios_admin'))

@admin_bp.route("/partidos/editar/<int:id>", methods=["GET", "POST"])
def editar_partido(id):
    partido = db.session.get(Partido, id)
    if request.method == "POST":
        partido.torneo_id = request.form.get("torneo_id")
        partido.inscripcion_1_id = request.form.get("inscripcion_1_id")
        partido.inscripcion_2_id = request.form.get("inscripcion_2_id")

        if partido.inscripcion_1_id == partido.inscripcion_2_id:
            flash("Error: Un equipo no puede jugar contra sí mismo.", "error")
            return redirect(url_for('admin.editar_partido', id=id))
        
        cancha_sel = request.form.get("cancha_id")
        partido.cancha_id = cancha_sel if cancha_sel else None
        partido.jornada = request.form.get("jornada")
        
        partido.tipo_partido = request.form.get("tipo_partido")
        
        f_hora_str = request.form.get("fecha_hora")
        if f_hora_str:
            partido.fecha_hora = datetime.strptime(f_hora_str, "%Y-%m-%dT%H:%M")
        db.session.commit()
        registrar_movimiento('Partidos', f'Se editó el partido ID: {partido.id}')
        return redirect(url_for('admin.vista_partidos_admin'))

    torneos = db.session.execute(db.select(Torneo).where(Torneo.activo==True)).scalars().all()
    canchas = db.session.execute(db.select(Cancha)).scalars().all()
    inscripciones = db.session.execute(db.select(Inscripcion)).scalars().all()

    return render_template("admin/editar_partido.html", partido=partido, torneos=torneos, canchas=canchas, inscripciones=inscripciones)

@admin_bp.route("/partidos/eliminar/<int:id>")
def eliminar_partido(id):
    partido = db.session.get(Partido, id)
    if partido:
        id_partido = partido.id
        db.session.delete(partido)
        db.session.commit()
        registrar_movimiento('Partidos', f'Se eliminó el partido ID: {id_partido}')
    return redirect(url_for('admin.vista_partidos_admin'))

# -----------------------------
# JUGADORES
# -----------------------------

@admin_bp.route("/jugadores")
def vista_jugadores_admin():
    jugadores_db = db.session.execute(db.select(Jugador)).scalars().all()
    return render_template("admin/jugadores_admin.html", jugadores=jugadores_db)

@admin_bp.route("/jugadores/nuevo", methods=["GET", "POST"])
def crear_jugador():
    if request.method == "POST":
        f_nac_str = request.form.get("fecha_nacimiento")
        f_nac_obj = datetime.strptime(f_nac_str, "%Y-%m-%d").date() if f_nac_str else None
        
        foto = request.files.get('foto_archivo')
        ruta_para_bd = None

        if foto and foto.filename:
            nombre_seguro = secure_filename(foto.filename)
            ruta_guardado = os.path.join('static', 'uploads', nombre_seguro)
            os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
            foto.save(ruta_guardado)
            ruta_para_bd = f'uploads/{nombre_seguro}'

        nuevo_jugador = Jugador(
            nombre=request.form.get("nombre"),
            apellido_paterno=request.form.get("apellido_paterno"),
            apellido_materno=request.form.get("apellido_materno"),
            fecha_nacimiento=f_nac_obj,
            sexo=request.form.get("sexo"),
            curp=request.form.get("curp") or None,
            foto_url=ruta_para_bd 
        )
        
        nombre_c = request.form.get("nombre_contacto")
        tel_c = request.form.get("telefono_contacto")
        par_c = request.form.get("parentesco")
        if nombre_c and tel_c and par_c:
            nuevo_jugador.contacto_emergencia = ContactoEmergencia(nombre_contacto=nombre_c, telefono=tel_c, parentesco=par_c)

        db.session.add(nuevo_jugador)
        db.session.commit()
        registrar_movimiento('Jugadores', f'Alta de jugador: {nuevo_jugador.nombre} {nuevo_jugador.apellido_paterno}')
        return redirect(url_for('admin.vista_jugadores_admin'))
    return render_template("admin/form_jugador.html")

@admin_bp.route("/jugadores/editar/<int:id>", methods=["GET", "POST"])
def editar_jugador(id):
    jugador = db.session.get(Jugador, id)
    if request.method == "POST":
        jugador.nombre = request.form.get("nombre")
        jugador.apellido_paterno = request.form.get("apellido_paterno")
        jugador.apellido_materno = request.form.get("apellido_materno")
        f_nac_str = request.form.get("fecha_nacimiento")
        jugador.fecha_nacimiento = datetime.strptime(f_nac_str, "%Y-%m-%d").date() if f_nac_str else None
        jugador.sexo = request.form.get("sexo")
        jugador.curp = request.form.get("curp") or None
        
        foto = request.files.get('foto_archivo')
        
        if foto and foto.filename:
            nombre_seguro = secure_filename(foto.filename)
            ruta_guardado = os.path.join('static', 'uploads', nombre_seguro)
            
            os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
            foto.save(ruta_guardado)
            
            jugador.foto_url = f'uploads/{nombre_seguro}'
        
        nombre_c = request.form.get("nombre_contacto")
        if jugador.contacto_emergencia:
            jugador.contacto_emergencia.nombre_contacto = nombre_c
            jugador.contacto_emergencia.telefono = request.form.get("telefono_contacto")
            jugador.contacto_emergencia.parentesco = request.form.get("parentesco")
        
        db.session.commit()
        registrar_movimiento('Jugadores', f'Se editó al jugador: {jugador.nombre}')
        return redirect(url_for('admin.vista_jugadores_admin'))
    return render_template("admin/editar_jugador.html", jugador=jugador)

@admin_bp.route("/jugadores/eliminar/<int:id>")
def eliminar_jugador(id):
    jugador = db.session.get(Jugador, id)
    if jugador:
        nom_completo = f"{jugador.nombre} {jugador.apellido_paterno}"
        db.session.delete(jugador)
        db.session.commit()
        registrar_movimiento('Jugadores', f'Se eliminó al jugador: {nom_completo}')
    return redirect(url_for('admin.vista_jugadores_admin'))

# -----------------------------
# INSCRIPCIONES Y ROSTER
# -----------------------------

@admin_bp.route("/inscripciones")
def vista_inscripciones_admin():
    inscripciones_db = db.session.execute(db.select(Inscripcion)).scalars().all()
    return render_template("admin/inscripciones_admin.html", inscripciones=inscripciones_db)

@admin_bp.route("/inscripciones/nueva", methods=["GET", "POST"])
def crear_inscripcion():
    if request.method == "POST":
        nueva_insc = Inscripcion(
            torneo_id=request.form.get("torneo_id"),
            equipo_id=request.form.get("equipo_id"),
            estado_inscripcion=request.form.get("estado_inscripcion")
        )
        db.session.add(nueva_insc)
        db.session.commit()
        registrar_movimiento('Inscripciones', f'Equipo ID {nueva_insc.equipo_id} inscrito al Torneo ID {nueva_insc.torneo_id}')
        return redirect(url_for('admin.vista_inscripciones_admin'))
    torneos = db.session.execute(db.select(Torneo).where(Torneo.activo==True)).scalars().all()
    equipos = db.session.execute(db.select(Equipo).where(Equipo.activo==True)).scalars().all()
    return render_template("admin/form_inscripcion.html", torneos=torneos, equipos=equipos)

@admin_bp.route("/inscripciones/editar/<int:id>", methods=["GET", "POST"])
def editar_inscripcion(id):
    inscripcion = db.session.get(Inscripcion, id)
    if request.method == "POST":
        inscripcion.estado_inscripcion = request.form.get("estado_inscripcion")
        db.session.commit()
        registrar_movimiento('Inscripciones', f'Se cambió estado de inscripción ID: {inscripcion.id}')
        return redirect(url_for('admin.vista_inscripciones_admin'))
    return render_template("admin/editar_inscripcion.html", inscripcion=inscripcion)

@admin_bp.route("/inscripciones/eliminar/<int:id>")
def eliminar_inscripcion(id):
    inscripcion = db.session.get(Inscripcion, id)
    if inscripcion:
        id_insc = inscripcion.id
        db.session.delete(inscripcion)
        db.session.commit()
        registrar_movimiento('Inscripciones', f'Se eliminó la inscripción ID: {id_insc}')
    return redirect(url_for('admin.vista_inscripciones_admin'))

@admin_bp.route("/inscripciones/<int:id>/roster", methods=["GET", "POST"])
def gestionar_roster(id):
    inscripcion = db.session.get(Inscripcion, id)
    if request.method == "POST":
        jugador_id = request.form.get("jugador_id")
        
        conflicto = db.session.execute(
            db.select(RegistroJugador)
            .join(Inscripcion)
            .where(Inscripcion.torneo_id == inscripcion.torneo_id)
            .where(RegistroJugador.jugador_id == int(jugador_id))
        ).scalar_one_or_none()
        if conflicto:
            flash("Error: ese jugador ya pertenece a otro equipo en este torneo.")
            return redirect(url_for('admin.gestionar_roster', id=inscripcion.id))

        es_capitan_form = True if request.form.get("es_capitan") else False

        if es_capitan_form:
            capitanes_anteriores = db.session.execute(
                db.select(RegistroJugador)
                .where(RegistroJugador.inscripcion_id == inscripcion.id)
                .where(RegistroJugador.es_capitan == True)
            ).scalars().all()
            
            for capitan in capitanes_anteriores:
                capitan.es_capitan = False

            inscripcion.equipo.capitan_id = jugador_id    

        nuevo_registro = RegistroJugador(
            inscripcion_id=inscripcion.id,
            jugador_id=jugador_id,
            dorsal=request.form.get("dorsal"),
            es_capitan=es_capitan_form
        )
        db.session.add(nuevo_registro)
        db.session.commit()
        registrar_movimiento('Plantillas', f'Jugador ID {nuevo_registro.jugador_id} agregado a {inscripcion.equipo.nombre}')
        return redirect(url_for('admin.gestionar_roster', id=inscripcion.id))

    todos_los_registros = db.session.execute(db.select(RegistroJugador)).scalars().all()
    ids_ocupados = [reg.jugador_id for reg in todos_los_registros if reg.inscripcion.torneo_id == inscripcion.torneo_id]
    todos_los_jugadores = db.session.execute(db.select(Jugador)).scalars().all()
    jugadores_libres = [j for j in todos_los_jugadores if j.id not in ids_ocupados]

    return render_template("admin/gestionar_roster.html", inscripcion=inscripcion, jugadores=jugadores_libres)

@admin_bp.route("/quitar_jugador_inscripcion/<int:registro_id>", methods=["GET", "POST"])
@login_required
def quitar_jugador_inscripcion(registro_id):
    registro = db.session.get(RegistroJugador, registro_id)
    if registro:
        inscripcion_id = registro.inscripcion_id
        equipo = registro.inscripcion.equipo 

        if equipo.capitan_id == registro.jugador_id:
            equipo.capitan_id = None 

        db.session.delete(registro)
        db.session.commit()
        registrar_movimiento('Plantillas', f'Jugador removido del equipo {equipo.nombre}')
        return redirect(url_for('admin.gestionar_roster', id=inscripcion_id))
        
    return redirect(request.referrer)

# -----------------------------
# ÁRBITROS
# -----------------------------

@admin_bp.route("/arbitros")
def vista_arbitros_admin():
    arbitros_db = db.session.execute(db.select(Arbitro)).scalars().all()
    return render_template("admin/arbitros_admin.html", arbitros=arbitros_db)

@admin_bp.route("/arbitros/nuevo", methods=["GET", "POST"])
def crear_arbitro():
    if request.method == "POST":
        nuevo_arbitro = Arbitro(
            nombre=request.form.get("nombre"),
            apellido_paterno=request.form.get("apellido_paterno"),
            apellido_materno=request.form.get("apellido_materno"),
            telefono=request.form.get("telefono"),
            estado=request.form.get("estado")
        )
        db.session.add(nuevo_arbitro)
        db.session.commit()
        registrar_movimiento('Árbitros', f'Alta de árbitro: {nuevo_arbitro.nombre} {nuevo_arbitro.apellido_paterno}')
        return redirect(url_for('admin.vista_arbitros_admin'))
    return render_template("admin/form_arbitro.html")

@admin_bp.route("/arbitros/editar/<int:id>", methods=["GET", "POST"])
def editar_arbitro(id):
    arbitro = db.session.get(Arbitro, id)
    if request.method == "POST":
        arbitro.nombre = request.form.get("nombre")
        arbitro.apellido_paterno = request.form.get("apellido_paterno")
        arbitro.apellido_materno = request.form.get("apellido_materno")
        arbitro.telefono = request.form.get("telefono")
        arbitro.estado = request.form.get("estado")
        db.session.commit()
        registrar_movimiento('Árbitros', f'Se editó al árbitro: {arbitro.nombre}')
        return redirect(url_for('admin.vista_arbitros_admin'))
    return render_template("admin/editar_arbitro.html", arbitro=arbitro)

@admin_bp.route("/arbitros/eliminar/<int:id>")
def eliminar_arbitro(id):
    arbitro = db.session.get(Arbitro, id)
    if arbitro:
        nom_arb = arbitro.nombre
        db.session.delete(arbitro)
        db.session.commit()
        registrar_movimiento('Árbitros', f'Se eliminó al árbitro: {nom_arb}')
    return redirect(url_for('admin.vista_arbitros_admin'))

# -----------------------------
# RESULTADOS E INCIDENCIAS
# -----------------------------

@admin_bp.route("/partidos/<int:id>/resultados", methods=["GET", "POST"])
def resultados_partido(id):
    partido = db.session.get(Partido, id)
    if request.method == "POST":
        nuevo_estado = request.form.get("estado")
        no_presento_1 = True if request.form.get("no_presento_1") else False
        no_presento_2 = True if request.form.get("no_presento_2") else False
        motivo_cancelacion = request.form.get("motivo_cancelacion")

        if nuevo_estado:
            partido.estado = nuevo_estado
            partido.motivo_cancelacion = motivo_cancelacion or partido.motivo_cancelacion

            if nuevo_estado in ("Cancelado", "Reprogramado"):
                for insc_id in [partido.inscripcion_1_id, partido.inscripcion_2_id]:
                    pago_arb = PagoArbitraje(
                        partido_id=partido.id,
                        inscripcion_id=insc_id,
                        fecha_pago=date_type.today(),
                        monto=COSTO_ARBITRAJE,
                        metodo_pago="Pendiente"
                    )
                    db.session.add(pago_arb)
                db.session.commit()
                registrar_movimiento('Partidos', f'Partido ID {partido.id} {nuevo_estado} — arbitraje generado automáticamente')
            else:
                db.session.commit()
                registrar_movimiento('Partidos', f'Estado del partido ID {partido.id} cambiado a {nuevo_estado}')

        if no_presento_1 or no_presento_2:
            partido.no_presento_1 = no_presento_1
            partido.no_presento_2 = no_presento_2
            partido.estado = "Finalizado"
            db.session.commit()
            registrar_movimiento('Partidos', f'No presentación registrada en partido ID {partido.id}')
            return redirect(url_for('admin.resultados_partido', id=partido.id))
            
        registro_jugador_id = request.form.get("registro_jugador_id")
        if registro_jugador_id:
            nuevo_gol = Gol(partido_id=partido.id, registro_jugador_id=registro_jugador_id)
            db.session.add(nuevo_gol)
            db.session.commit()
            registrar_movimiento('Estadísticas', f'Gol registrado en partido ID {partido.id}')

        tipo_incidencia = request.form.get("tipo_incidencia")
        if tipo_incidencia:
            nueva_incidencia = Incidencia(
                partido_id=partido.id,
                registro_jugador_id=request.form.get("jugador_incidencia_id"),
                tipo=tipo_incidencia,
                descripcion=request.form.get("descripcion", "Sin detalles")
            )
            db.session.add(nueva_incidencia)
            db.session.commit()
            registrar_movimiento('Estadísticas', f'Incidencia ({tipo_incidencia}) registrada en partido ID {partido.id}')

        return redirect(url_for('admin.resultados_partido', id=partido.id))
    return render_template("admin/resultados_partido.html", partido=partido)


@admin_bp.route("/partidos/<int:partido_id>/eliminar_gol/<int:gol_id>", methods=["POST"])
@login_required
def eliminar_gol(partido_id, gol_id):
    gol = db.session.get(Gol, gol_id) 
    if gol:
        db.session.delete(gol)
        db.session.commit()
        registrar_movimiento('Partidos', f'Se eliminó un gol del partido {partido_id}')
    return redirect(url_for('admin.resultados_partido', id=partido_id))

@admin_bp.route("/partidos/<int:partido_id>/eliminar_incidencia/<int:incidencia_id>", methods=["POST"])
@login_required
def eliminar_incidencia(partido_id, incidencia_id):
    incidencia = db.session.get(Incidencia, incidencia_id)
    if incidencia:
        db.session.delete(incidencia)
        db.session.commit()
        registrar_movimiento('Partidos', f'Se eliminó una incidencia del partido {partido_id}')
    return redirect(url_for('admin.resultados_partido', id=partido_id))

# -----------------------------
# ADEUDOS
# -----------------------------

@admin_bp.get("/adeudos")
def vista_adeudos_admin():
    inscripciones_sin_pago = db.session.execute(
        db.select(Inscripcion)
        .where(Inscripcion.estado_inscripcion != "Pagada")
    ).scalars().all()

    arbitrajes_pendientes = db.session.execute(
        db.select(PagoArbitraje)
        .where(PagoArbitraje.metodo_pago == "Pendiente")
    ).scalars().all()

    return render_template(
        "admin/adeudos_admin.html",
        inscripciones_sin_pago=inscripciones_sin_pago,
        arbitrajes_pendientes=arbitrajes_pendientes
    )

@admin_bp.route("/adeudos/inscripcion/pagar/<int:id>", methods=["POST"])
@login_required
def pagar_inscripcion_rapido(id):
    inscripcion = db.session.get(Inscripcion, id)
    if inscripcion:
        inscripcion.estado_inscripcion = "Pagada"
        db.session.commit()
        registrar_movimiento('Adeudos', f'Inscripción ID {inscripcion.id} marcada como pagada')
    return redirect(url_for('admin.vista_adeudos_admin'))

@admin_bp.route("/partidos/<int:partido_id>/pagar_arbitraje_equipo/<int:inscripcion_id>", methods=["POST"])
@login_required
def pagar_arbitraje_equipo(partido_id, inscripcion_id):
    metodo = request.form.get("metodo_pago", "Efectivo")
    monto_ingresado = float(request.form.get("monto", 0))
    
    pago_pendiente = db.session.execute(
        db.select(PagoArbitraje)
        .where(PagoArbitraje.partido_id == partido_id)
        .where(PagoArbitraje.inscripcion_id == inscripcion_id)
        .where(PagoArbitraje.metodo_pago == "Pendiente")
    ).scalars().first()
    
    if pago_pendiente:
        monto_original = float(pago_pendiente.monto)
        
        if monto_ingresado >= monto_original:
            pago_pendiente.metodo_pago = metodo
            pago_pendiente.fecha_pago = date_type.today()
            pago_pendiente.monto = monto_ingresado
        else:
            pago_pendiente.metodo_pago = metodo
            pago_pendiente.fecha_pago = date_type.today()
            pago_pendiente.monto = monto_ingresado
            
            nuevo_pendiente = PagoArbitraje(
                partido_id=partido_id,
                inscripcion_id=inscripcion_id,
                fecha_pago=date_type.today(),
                monto=(monto_original - monto_ingresado),
                metodo_pago="Pendiente"
            )
            db.session.add(nuevo_pendiente)
            
        db.session.commit()
        registrar_movimiento('Adeudos', f'Abono de ${monto_ingresado} en partido {partido_id}')

    url_volver = request.referrer or url_for('admin.resultados_partido', id=partido_id)
    return redirect(url_volver)

# =========================================
# LIGUILLA Y CALENDARIO AUTOMÁTICO (BERGER)
# =========================================

@admin_bp.route("/torneos/<int:torneo_id>/generar_calendario", methods=["POST"])
@login_required
def generar_calendario(torneo_id):
    torneo = db.session.get(Torneo, torneo_id)
    if not torneo:
        flash("Torneo no encontrado.", "error")
        return redirect(url_for('admin.vista_torneos_admin'))

    # 1. Validar que no se duplique la creación
    partidos_existentes = db.session.execute(
        db.select(Partido)
        .where(Partido.torneo_id == torneo_id)
        .where(Partido.tipo_partido == "Fase Regular")
    ).scalars().first()
    if partidos_existentes:
        flash("El calendario de fase regular ya fue generado previamente.", "error")
        return redirect(url_for('admin.vista_torneos_admin'))

    inscripciones = db.session.execute(
        db.select(Inscripcion).where(Inscripcion.torneo_id == torneo_id)
    ).scalars().all()

    if len(inscripciones) < 3:
        flash("Se necesitan al menos 3 equipos inscritos para generar un calendario de todos contra todos.", "error")
        return redirect(url_for('admin.vista_torneos_admin'))

    # 2. Configurar Equipos y el "Descanso" si son impares
    equipos = [insc.id for insc in inscripciones]
    if len(equipos) % 2 != 0:
        equipos.append(None) # None actuará como el equipo "Descanso"

    n = len(equipos)
    total_jornadas = n - 1
    partidos_por_jornada = n // 2

    # 3. Calcular la fecha base del torneo
    hoy = datetime.now().date()
    # Si el torneo no tiene fecha de inicio, la asignamos para la siguiente semana
    fecha_base = torneo.fecha_inicio if torneo.fecha_inicio else hoy + timedelta(days=1)
    
    # Buscar el próximo día que coincida con la configuración del torneo
    while True:
        wd = fecha_base.weekday()
        if torneo.dia_torneo == "Domingo" and wd == 6: break
        elif torneo.dia_torneo == "Sabatino" and wd == 5: break
        elif torneo.dia_torneo == "Lunes-Viernes" and wd < 5: break
        elif not torneo.dia_torneo and wd == 5: break # Sábado por defecto
        fecha_base += timedelta(days=1)

    # 4. Generar el Calendario (Algoritmo de Berger)
    for jornada in range(total_jornadas):
        # A cada jornada le sumamos 1 semana de diferencia
        fecha_jornada = fecha_base + timedelta(weeks=jornada)
        
        # Empezamos los partidos de ese día a las 08:00 AM
        hora_inicio = datetime(fecha_jornada.year, fecha_jornada.month, fecha_jornada.day, 8, 0)
        hora_actual = hora_inicio

        for i in range(partidos_por_jornada):
            local = equipos[i]
            visitante = equipos[n - 1 - i]

            # Intercalar quién es local y visitante para el equipo fijo (índice 0)
            if jornada % 2 == 1 and i == 0:
                local, visitante = visitante, local

            # Si a uno de los dos le toca el equipo "Descanso", ignoramos el cruce
            if local is not None and visitante is not None:
                nuevo_partido = Partido(
                    torneo_id=torneo_id,
                    inscripcion_1_id=local,
                    inscripcion_2_id=visitante,
                    fecha_hora=hora_actual,
                    jornada=f"Jornada {jornada + 1}",
                    tipo_partido="Fase Regular",
                    estado="Programado"
                )
                db.session.add(nuevo_partido)
                db.session.flush() # Para obtener el ID del partido antes de guardar los adeudos
                
                # Generamos automáticamente el pago del arbitraje para ambos equipos
                pago_arb_1 = PagoArbitraje(
                    partido_id=nuevo_partido.id,
                    inscripcion_id=local,
                    fecha_pago=date_type.today(),
                    monto=COSTO_ARBITRAJE,
                    metodo_pago="Pendiente"
                )
                pago_arb_2 = PagoArbitraje(
                    partido_id=nuevo_partido.id,
                    inscripcion_id=visitante,
                    fecha_pago=date_type.today(),
                    monto=COSTO_ARBITRAJE,
                    metodo_pago="Pendiente"
                )
                db.session.add(pago_arb_1)
                db.session.add(pago_arb_2)

                # El siguiente partido se programa 2 horas después
                hora_actual += timedelta(hours=2)

        # Rotación del algoritmo: dejamos el índice 0 fijo y movemos los demás
        equipos.insert(1, equipos.pop())

    db.session.commit()
    registrar_movimiento('Torneos', f'Se generó el calendario Fase Regular para {torneo.nombre}')
    flash(f"¡Calendario de la Fase Regular generado exitosamente para {len(inscripciones)} equipos!")
    return redirect(url_for('admin.vista_partidos_admin'))


@admin_bp.route("/torneos/<int:torneo_id>/generar_liguilla", methods=["POST"])
@login_required
def generar_liguilla(torneo_id):
    torneo = db.session.get(Torneo, torneo_id)
    if not torneo:
        flash("Torneo no encontrado.", "error")
        return redirect(url_for('admin.vista_torneos_admin'))

    partidos = db.session.execute(
        db.select(Partido)
        .where(Partido.torneo_id == torneo_id)
        .where(Partido.estado == "Finalizado")
        .where(Partido.tipo_partido == "Fase Regular") 
    ).scalars().all()

    stats = {}
    for p in partidos:
        for insc in [p.inscripcion_1, p.inscripcion_2]:
            if insc.id not in stats:
                stats[insc.id] = {"id": insc.id, "PJ": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0}

    for p in partidos:
        g1 = sum(1 for gol in p.goles if gol.registro_jugador and gol.registro_jugador.inscripcion_id == p.inscripcion_1_id)
        g2 = sum(1 for gol in p.goles if gol.registro_jugador and gol.registro_jugador.inscripcion_id == p.inscripcion_2_id)
        id1, id2 = p.inscripcion_1_id, p.inscripcion_2_id

        stats[id1]["GF"] += g1
        stats[id1]["GC"] += g2
        stats[id2]["GF"] += g2
        stats[id2]["GC"] += g1
        stats[id1]["PJ"] += 1
        stats[id2]["PJ"] += 1

        if g1 > g2:
            stats[id1]["G"] += 1
            stats[id2]["P"] += 1
        elif g1 == g2:
            stats[id1]["E"] += 1
            stats[id2]["E"] += 1
        else:
            stats[id2]["G"] += 1
            stats[id1]["P"] += 1

    for s in stats.values():
        s["DG"] = s["GF"] - s["GC"]
        s["PTS"] = s["G"] * 3 + s["E"]

    tabla = sorted(stats.values(), key=lambda x: (x["PTS"], x["DG"]), reverse=True)

    clasificados = tabla[:8]
    n = len(clasificados)

    if n % 2 != 0:
        n -= 1
        clasificados = clasificados[:n]

    if n < 2:
        flash("No hay suficientes equipos con partidos jugados para armar liguilla.", "error")
        return redirect(url_for('admin.vista_torneos_admin'))

    hoy = datetime.now().date()
    dia_busqueda = hoy + timedelta(days=1)
    
    while True:
        wd = dia_busqueda.weekday() 
        if torneo.dia_torneo == "Domingo" and wd == 6:
            break
        elif torneo.dia_torneo == "Sabatino" and wd == 5:
            break
        elif torneo.dia_torneo == "Lunes-Viernes" and wd < 5:
            break
        elif not torneo.dia_torneo and wd == 5:
            break
            
        dia_busqueda += timedelta(days=1)

    fecha_base = datetime(dia_busqueda.year, dia_busqueda.month, dia_busqueda.day, 17, 0)

    for i in range(n // 2):
        id_loc = clasificados[i]["id"]
        id_vis = clasificados[n - 1 - i]["id"]
        
        nuevo_p = Partido(
            torneo_id=torneo_id,
            inscripcion_1_id=id_loc,
            inscripcion_2_id=id_vis,
            fecha_hora=fecha_base + timedelta(hours=i), 
            jornada="Cuartos de Final" if n >= 8 else "Liguilla",
            tipo_partido="Liguilla", 
            estado="Programado"
        )
        db.session.add(nuevo_p)

    db.session.commit()
    registrar_movimiento('Torneos', f'Liguilla generada para {torneo.nombre} ({n} equipos)')
    flash("¡Liguilla armada con éxito!")
    return redirect(url_for('admin.vista_partidos_admin'))


@admin_bp.route("/cambiar_rol_roster/<int:registro_id>", methods=["POST"])
@login_required
def cambiar_rol_roster(registro_id):
    registro = db.session.get(RegistroJugador, registro_id)
    
    if registro:
        inscripcion = registro.inscripcion
        equipo = inscripcion.equipo

        if registro.es_capitan:
            registro.es_capitan = False
            
            if equipo.capitan_id == registro.jugador_id:
                equipo.capitan_id = None
                
            flash(f"Se le ha quitado la capitanía a {registro.jugador.nombre}.", "info")
            
        else:
            capitanes_anteriores = db.session.execute(
                db.select(RegistroJugador)
                .where(RegistroJugador.inscripcion_id == inscripcion.id)
                .where(RegistroJugador.es_capitan == True)
            ).scalars().all()
            
            for capitan_antiguo in capitanes_anteriores:
                capitan_antiguo.es_capitan = False
                
            registro.es_capitan = True
            equipo.capitan_id = registro.jugador_id
            
            flash(f"{registro.jugador.nombre} es el nuevo capitán del equipo.", "success")

        db.session.commit()
        return redirect(url_for('admin.gestionar_roster', id=inscripcion.id))
        
    return redirect(request.referrer)