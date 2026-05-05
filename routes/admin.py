from datetime import datetime, date as date_type
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
    
    # Traemos los movimientos para el dashboard
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
    torneos_db = db.session.execute(db.select(Torneo)).scalars().all()
    return render_template("admin/torneos_admin.html", torneos=torneos_db)

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
    total_goles = db.session.scalar(db.select(func.count(Gol.id))) or 0
    total_amarillas = db.session.scalar(db.select(func.count(Incidencia.id)).where(Incidencia.tipo == "Tarjeta Amarilla")) or 0
    total_rojas = db.session.scalar(db.select(func.count(Incidencia.id)).where(Incidencia.tipo == "Tarjeta Roja")) or 0

    top_goleadores_query = (
        db.select(
            Jugador.nombre,
            Jugador.apellido_paterno,
            Equipo.nombre.label('equipo_nombre'),
            func.count(Gol.id).label('total_goles')
        )
        .select_from(Gol)
        .join(RegistroJugador, Gol.registro_jugador_id == RegistroJugador.id)
        .join(Jugador, RegistroJugador.jugador_id == Jugador.id)
        .join(Inscripcion, RegistroJugador.inscripcion_id == Inscripcion.id)
        .join(Equipo, Inscripcion.equipo_id == Equipo.id)
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
            estado="Visible"
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
            representante=request.form.get("representante"),
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
        cancha_id = request.form.get("cancha_id")
        fecha_hora_str = request.form.get("fecha_hora")
        jornada = request.form.get("jornada")
        
        # Convertimos el texto del formulario a un objeto de Fecha y Hora de Python
        fecha_hora_obj = datetime.strptime(fecha_hora_str, "%Y-%m-%dT%H:%M")

        nuevo_partido = Partido( 
            torneo_id=torneo_id,
            inscripcion_1_id=inscripcion_1_id,
            inscripcion_2_id=inscripcion_2_id,
            cancha_id=cancha_id,
            fecha_hora=fecha_hora_obj,
            jornada=request.form.get("jornada"),
            estado="Programado",
            arbitro_id=request.form.get("arbitro_id") if request.form.get("arbitro_id") else None
        )
        db.session.add(nuevo_partido)
        db.session.commit()
        registrar_movimiento('Partidos', f'Partido programado ID: {nuevo_partido.id}')
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
        equipo.representante = request.form.get("representante")
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
        # Si no seleccionan cancha, guardamos None
        cancha_sel = request.form.get("cancha_id")
        partido.cancha_id = cancha_sel if cancha_sel else None
        partido.jornada = request.form.get("jornada")
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
        nuevo_jugador = Jugador(
            nombre=request.form.get("nombre"),
            apellido_paterno=request.form.get("apellido_paterno"),
            apellido_materno=request.form.get("apellido_materno"),
            fecha_nacimiento=f_nac_obj,
            sexo=request.form.get("sexo"),
            curp=request.form.get("curp") or None,
            foto_url=request.form.get("foto_url") or None
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
        jugador.foto_url = request.form.get("foto_url") or None
        
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
        # Validar que el jugador no pertenezca ya a otro equipo en el mismo torneo
        conflicto = db.session.execute(
            db.select(RegistroJugador)
            .join(Inscripcion)
            .where(Inscripcion.torneo_id == inscripcion.torneo_id)
            .where(RegistroJugador.jugador_id == int(jugador_id))
        ).scalar_one_or_none()
        if conflicto:
            flash("Error: ese jugador ya pertenece a otro equipo en este torneo.")
            return redirect(url_for('admin.gestionar_roster', id=inscripcion.id))

        nuevo_registro = RegistroJugador(
            inscripcion_id=inscripcion.id,
            jugador_id=jugador_id,
            dorsal=request.form.get("dorsal"),
            es_capitan=True if request.form.get("es_capitan") else False
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

@admin_bp.route("/inscripciones/quitar_jugador/<int:registro_id>")
def quitar_jugador_inscripcion(registro_id):
    registro = db.session.get(RegistroJugador, registro_id)
    if registro:
        insc_id = registro.inscripcion_id
        nom_jugador = registro.jugador.nombre
        db.session.delete(registro)
        db.session.commit()
        registrar_movimiento('Plantillas', f'Se quitó a {nom_jugador} de la plantilla')
        return redirect(url_for('admin.gestionar_roster', id=insc_id))
    return redirect(url_for('admin.vista_inscripciones_admin'))

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

            # Auto-generar pagos de arbitraje si se cancela o reprograma
            if nuevo_estado in ("Cancelado", "Reprogramado"):
                from datetime import date as _date
                for insc_id in [partido.inscripcion_1_id, partido.inscripcion_2_id]:
                    pago_arb = PagoArbitraje(
                        partido_id=partido.id,
                        inscripcion_id=insc_id,
                        fecha_pago=_date.today(),
                        monto=COSTO_ARBITRAJE,
                        metodo_pago="Pendiente"
                    )
                    db.session.add(pago_arb)
                db.session.commit()
                registrar_movimiento('Partidos', f'Partido ID {partido.id} {nuevo_estado} — arbitraje generado automáticamente')
            else:
                db.session.commit()
                registrar_movimiento('Partidos', f'Estado del partido ID {partido.id} cambiado a {nuevo_estado}')

        # Manejar no presentaciones
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
    from models import PagoInscripcion
    inscripciones_sin_pago = db.session.execute(
        db.select(Inscripcion)
        .outerjoin(PagoInscripcion, PagoInscripcion.inscripcion_id == Inscripcion.id)
        .where(PagoInscripcion.id == None)
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

@admin_bp.route("/adeudos/arbitraje/pagar/<int:id>", methods=["POST"])
def pagar_arbitraje(id):
    from datetime import date as _date
    pago = db.session.get(PagoArbitraje, id)
    if pago:
        pago.metodo_pago = request.form.get("metodo_pago", "Efectivo")
        pago.fecha_pago = _date.today()
        db.session.commit()
        registrar_movimiento('Adeudos', f'Arbitraje ID {pago.id} marcado como pagado')
    return redirect(url_for('admin.vista_adeudos_admin'))