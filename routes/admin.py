from datetime import datetime
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required
from db import db
from models import Torneo, Equipo, Cancha, Partido, Anuncio, Jugador, Inscripcion, RegistroJugador, ContactoEmergencia, Arbitro, LogActividad

admin_bp = Blueprint("admin", __name__)


def registrar_movimiento(modulo, movimiento, estatus='Aplicado'):
    nuevo_log = LogActividad(
        modulo=modulo,
        movimiento=movimiento,
        responsable="Admin",  # Aquí podrías usar current_user.username si quieres registrar quién hizo el movimiento
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
    #  Contamos los Torneos Activos
    torneos_activos = len(db.session.execute(db.select(Torneo).where(Torneo.activo==True)).scalars().all())
    
    #  Contamos Todos los Equipos
    equipos_registrados = len(db.session.execute(db.select(Equipo)).scalars().all())
    
    # Contamos los Partidos Programados (si aún no tienes la tabla Partido funcionando, puedes dejarlo en 0 temporalmente)
    partidos_programados = len(db.session.execute(db.select(Partido).where(Partido.estado=='Programado')).scalars().all())
    
    #  Contamos Anuncios Activos
    anuncios_activos = len(db.session.execute(db.select(Anuncio).where(Anuncio.estado=='Visible')).scalars().all())

    return render_template("admin/dashboard.html", 
                            tot_torneos=torneos_activos, 
                            tot_equipos=equipos_registrados, 
                            tot_partidos=partidos_programados, 
                            tot_anuncios=anuncios_activos)

@admin_bp.get("/login")
def login_admin():
    return render_template("admin/login_admin.html")

@admin_bp.get("/torneos")
def vista_torneos_admin():
    # Leemos todos los torneos de la base de datos
    torneos_db = db.session.execute(db.select(Torneo)).scalars().all()
    return render_template("admin/torneos_admin.html", torneos=torneos_db)

@admin_bp.get("/equipos")
def vista_equipos_admin():
    equipos_db = db.session.execute(db.select(Equipo)).scalars().all()
    return render_template("admin/equipos_admin.html", equipos=equipos_db)

@admin_bp.get("/partidos")
def vista_partidos_admin():
    partidos_db = db.session.execute(db.select(Partido)).scalars().all()
    return render_template("admin/partidos_admin.html", partidos=partidos_db)

@admin_bp.get("/canchas")
def vista_canchas_admin():
    canchas_db = db.session.execute(db.select(Cancha)).scalars().all() # leer las canchas de la bd
    return render_template("admin/canchas_admin.html", canchas=canchas_db) #mandarselas al html

@admin_bp.get("/estadisticas")
def vista_estadisticas_admin():
    return render_template("admin/estadisticas_admin.html")

@admin_bp.get("/anuncios")
def vista_anuncios_admin():
    anuncios_db = db.session.execute(db.select(Anuncio)).scalars().all()
    return render_template("admin/anuncios_admin.html", anuncios=anuncios_db)


# -----------------------------
# API ADMIN                 Este pedazo no se si se va a usar o no nomas o dejo por si acaso
# -----------------------------
# @admin_bp.post("/torneos")
# @login_required
# def crear_torneo():
#     data = request.get_json(silent=True) or {}

#     nombre = data.get("nombre", "").strip()
#     if not nombre:
#         return jsonify({"ok": False, "error": "El nombre es obligatorio"}), 400

#     torneo = Torneo(
#         nombre=nombre,
#         categoria=data.get("categoria"),
#         tipo=data.get("tipo"),
#         fecha_inicio=datetime.strptime(data["fecha_inicio"], "%Y-%m-%d").date() if data.get("fecha_inicio") else None,
#         fecha_fin=datetime.strptime(data["fecha_fin"], "%Y-%m-%d").date() if data.get("fecha_fin") else None,
#         activo=data.get("activo", True)
#     )

#     db.session.add(torneo)
#     db.session.commit()

#     return jsonify({"ok": True, "id": torneo.id, "mensaje": "Torneo creado"}), 201


#-------------------------------------------------------------------------------------------------------------------------------
#--------
# Rutas que conectaran los formularios a la bd y luego redireccionaran a las vistas correspondientes
#--------

@admin_bp.route("/canchas/nueva", methods=["GET", "POST"])
def crear_cancha():
    if request.method == "POST":
        # lo que el usuario escribio en el formulario
        nombre = request.form.get("nombre")
        ubicacion = request.form.get("ubicacion")
        tipo = request.form.get("tipo")
        
        # crear objeto cancha y guardarlo en la db
        nueva_cancha = Cancha(
            nombre=nombre, 
            ubicacion=ubicacion, 
            tipo=tipo, 
            disponibilidad="Disponible" 
        )
        db.session.add(nueva_cancha)
        db.session.commit()
        
        registrar_movimiento('Canchas', f'Alta de cancha: {nueva_cancha.nombre}', 'Aplicado')
        

        flash("¡Cancha agregada exitosamente!")
        return redirect(url_for('admin.vista_canchas_admin'))

    
    return render_template("admin/form_cancha.html")

@admin_bp.route("/anuncios/nuevo", methods=["GET", "POST"])
def crear_anuncio():
    if request.method == "POST":
        titulo = request.form.get("titulo")
        contenido = request.form.get("contenido")
        fecha = request.form.get("fecha_publicacion")
        
        nuevo_anuncio = Anuncio(
            titulo=titulo, 
            contenido=contenido, 
            fecha_publicacion=fecha,
            estado="Visible"
        )
        db.session.add(nuevo_anuncio)
        db.session.commit()
        
        registrar_movimiento('Anuncios', f'Alta de anuncio: {nuevo_anuncio.titulo}', 'Aplicado')
        return redirect(url_for('admin.vista_anuncios_admin'))

    return render_template("admin/form_anuncio.html")

@admin_bp.route("/torneos/nuevo", methods=["GET", "POST"])
def crear_torneo():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        categoria = request.form.get("categoria")
        tipo = request.form.get("tipo")
        fecha_inicio_str = request.form.get("fecha_inicio")
        fecha_fin_str = request.form.get("fecha_fin")
        
        # Convertir los textos del formulario a fechas reales de Python
        from datetime import datetime
        f_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date() if fecha_inicio_str else None
        f_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date() if fecha_fin_str else None

        nuevo_torneo = Torneo(
            nombre=nombre,
            categoria=categoria,
            tipo=tipo,
            fecha_inicio=f_inicio,
            fecha_fin=f_fin,
            activo=True # Por defecto está activo
        )
        db.session.add(nuevo_torneo)
        db.session.commit()
        
        registrar_movimiento('Torneos', f'Alta de {nuevo_torneo.nombre}', 'Aplicado')
    
        return redirect(url_for('admin.vista_torneos_admin'))

    return render_template("admin/form_torneo.html")


@admin_bp.route("/equipos/nuevo", methods=["GET", "POST"])
def crear_equipo():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        representante = request.form.get("representante")
        telefono = request.form.get("telefono")
        categoria = request.form.get("categoria")    


        nuevo_equipo = Equipo(
            nombre=nombre,
            representante=representante,
            telefono=telefono,
            categoria=categoria,
            activo=True
        )
        db.session.add(nuevo_equipo)
        db.session.commit()
        
        registrar_movimiento('Equipos', f'Alta de equipo: {nuevo_equipo.nombre}', 'Aplicado')
        return redirect(url_for('admin.vista_equipos_admin'))

    return render_template("admin/form_equipo.html")


@admin_bp.route("/partidos/nuevo", methods=["GET", "POST"])
def crear_partido():
    if request.method == "POST":
        torneo_id = request.form.get("torneo_id")
        local_id = request.form.get("local_id")
        visitante_id = request.form.get("visitante_id")
        cancha_id = request.form.get("cancha_id")
        fecha_hora_str = request.form.get("fecha_hora")
        jornada = request.form.get("jornada")
        
        # Convertimos el texto del formulario a un objeto de Fecha y Hora de Python
        fecha_hora_obj = datetime.strptime(fecha_hora_str, "%Y-%m-%dT%H:%M")

        nuevo_partido = Partido( 
            torneo_id=torneo_id,
            local_id=local_id,
            visitante_id=visitante_id,
            cancha_id=cancha_id,
            fecha_hora=fecha_hora_obj,
            jornada=jornada,
            estado="Programado"
        )
        db.session.add(nuevo_partido)
        db.session.commit()
        
        return redirect(url_for('admin.vista_partidos_admin'))

    # Si es GET (apenas va a abrir la pantalla), jalamos las opciones para los Select
    torneos = db.session.execute(db.select(Torneo).where(Torneo.activo==True)).scalars().all()
    equipos = db.session.execute(db.select(Equipo).where(Equipo.activo==True)).scalars().all()
    canchas = db.session.execute(db.select(Cancha)).scalars().all()

    return render_template("admin/form_partido.html", torneos=torneos, equipos=equipos, canchas=canchas)



# ==========================================
# editar eliminar canchas
# ==========================================
@admin_bp.route("/canchas/editar/<int:id>", methods=["GET", "POST"])
def editar_cancha(id):
    # Buscamos la cancha específica en la base de datos
    cancha = db.session.get(Cancha, id)
    
    if request.method == "POST":
        # Sobrescribimos los datos con lo nuevo que llegó del formulario
        cancha.nombre = request.form.get("nombre")
        cancha.ubicacion = request.form.get("ubicacion")
        cancha.tipo = request.form.get("tipo")
        cancha.disponibilidad = request.form.get("disponibilidad")
        
        db.session.commit() # Guardamos los cambios
        return redirect(url_for('admin.vista_canchas_admin'))

    # Si es GET, mostramos el formulario pre-llenado
    return render_template("admin/editar_cancha.html", cancha=cancha)

# Ruta para eliminar una cancha
@admin_bp.route("/canchas/eliminar/<int:id>")
def eliminar_cancha(id):
    cancha = db.session.get(Cancha, id)
    if cancha:
        db.session.delete(cancha)
        db.session.commit()
        registrar_movimiento('Canchas', f'Eliminación de cancha: {cancha.nombre}', 'Aplicado')
    return redirect(url_for('admin.vista_canchas_admin'))




# ==========================================
# editar eliminar torneos
# ==========================================
@admin_bp.route("/torneos/editar/<int:id>", methods=["GET", "POST"])
def editar_torneo(id):
    torneo = db.session.get(Torneo, id)
    if request.method == "POST":
        torneo.nombre = request.form.get("nombre")
        torneo.categoria = request.form.get("categoria")
        torneo.tipo = request.form.get("tipo")
        
        from datetime import datetime
        f_ini = request.form.get("fecha_inicio")
        f_fin = request.form.get("fecha_fin")
        torneo.fecha_inicio = datetime.strptime(f_ini, "%Y-%m-%d").date() if f_ini else None
        torneo.fecha_fin = datetime.strptime(f_fin, "%Y-%m-%d").date() if f_fin else None
        
        db.session.commit()
        return redirect(url_for('admin.vista_torneos_admin'))
    return render_template("admin/editar_torneo.html", torneo=torneo)

@admin_bp.route("/torneos/eliminar/<int:id>")
def eliminar_torneo(id):
    torneo = db.session.get(Torneo, id)
    if torneo:
        registrar_movimiento('Torneos', f'Eliminación de torneo: {torneo.nombre}', 'Aplicado')
        db.session.delete(torneo)
        db.session.commit()
    return redirect(url_for('admin.vista_torneos_admin'))

# ==========================================
# editar eliminar equipos
# ==========================================
@admin_bp.route("/equipos/editar/<int:id>", methods=["GET", "POST"])
def editar_equipo(id):
    equipo = db.session.get(Equipo, id)
    if request.method == "POST":
        equipo.nombre = request.form.get("nombre")
        equipo.representante = request.form.get("representante")
        equipo.telefono = request.form.get("telefono")
        equipo.categoria = request.form.get("categoria")
        db.session.commit()
        return redirect(url_for('admin.vista_equipos_admin'))
    return render_template("admin/editar_equipo.html", equipo=equipo)

@admin_bp.route("/equipos/eliminar/<int:id>")
def eliminar_equipo(id):
    equipo = db.session.get(Equipo, id)
    if equipo:
        db.session.delete(equipo)
        db.session.commit()
        registrar_movimiento('Equipos', f'Eliminación de equipo: {equipo.nombre}', 'Aplicado')
    return redirect(url_for('admin.vista_equipos_admin'))

# ==========================================
# Editar eliminar anuncios
# ==========================================
@admin_bp.route("/anuncios/editar/<int:id>", methods=["GET", "POST"])
def editar_anuncio(id):
    anuncio = db.session.get(Anuncio, id)
    if request.method == "POST":
        anuncio.titulo = request.form.get("titulo")
        anuncio.contenido = request.form.get("contenido")
        anuncio.fecha_publicacion = request.form.get("fecha_publicacion")
        db.session.commit()
        return redirect(url_for('admin.vista_anuncios_admin'))
    return render_template("admin/editar_anuncio.html", anuncio=anuncio)

@admin_bp.route("/anuncios/eliminar/<int:id>")
def eliminar_anuncio(id):
    anuncio = db.session.get(Anuncio, id)
    if anuncio:
        db.session.delete(anuncio)
        db.session.commit()
        registrar_movimiento('Anuncios', f'Eliminación de anuncio: {anuncio.titulo}', 'Aplicado')
    return redirect(url_for('admin.vista_anuncios_admin'))


# ==========================================
# Editar eliminar partidos
# ==========================================
@admin_bp.route("/partidos/editar/<int:id>", methods=["GET", "POST"])
def editar_partido(id):
    partido = db.session.get(Partido, id)
    
    if request.method == "POST":
        partido.torneo_id = request.form.get("torneo_id")
        partido.local_id = request.form.get("local_id")
        partido.visitante_id = request.form.get("visitante_id")
        # Si no seleccionan cancha, guardamos None
        cancha_sel = request.form.get("cancha_id")
        partido.cancha_id = cancha_sel if cancha_sel else None
        
        partido.jornada = request.form.get("jornada")
        # Registrar movimiento
        # Formatear la fecha y hora de nuevo
        from datetime import datetime
        f_hora_str = request.form.get("fecha_hora")
        if f_hora_str:
            partido.fecha_hora = datetime.strptime(f_hora_str, "%Y-%m-%dT%H:%M")
            
        db.session.commit()
        return redirect(url_for('admin.vista_partidos_admin'))

    # Si es GET, cargamos las listas para los menús desplegables
    torneos = db.session.execute(db.select(Torneo).where(Torneo.activo==True)).scalars().all()
    equipos = db.session.execute(db.select(Equipo).where(Equipo.activo==True)).scalars().all()
    canchas = db.session.execute(db.select(Cancha)).scalars().all()

    return render_template("admin/editar_partido.html", partido=partido, torneos=torneos, equipos=equipos, canchas=canchas)

@admin_bp.route("/partidos/eliminar/<int:id>")
def eliminar_partido(id):
    partido = db.session.get(Partido, id)
    if partido:
        db.session.delete(partido)
        db.session.commit()
    return redirect(url_for('admin.vista_partidos_admin'))


# ==========================================
# Todo lo de jugadores
# ==========================================

# 1ver jugaodres
@admin_bp.route("/jugadores")
def vista_jugadores_admin():
    jugadores_db = db.session.execute(db.select(Jugador)).scalars().all()
    return render_template("admin/jugadores_admin.html", jugadores=jugadores_db)


# Crear Jugador
@admin_bp.route("/jugadores/nuevo", methods=["GET", "POST"])
def crear_jugador():
    if request.method == "POST":
        # Datos del Jugador
        nombre = request.form.get("nombre")
        paterno = request.form.get("apellido_paterno")
        materno = request.form.get("apellido_materno")
        f_nac_str = request.form.get("fecha_nacimiento")
        sexo = request.form.get("sexo")

        from datetime import datetime
        f_nac_obj = datetime.strptime(f_nac_str, "%Y-%m-%d").date() if f_nac_str else None

        nuevo_jugador = Jugador(
            nombre=nombre,
            apellido_paterno=paterno,
            apellido_materno=materno,
            fecha_nacimiento=f_nac_obj,
            sexo=sexo
        )
        
        # Datos del Contacto de Emergencia
        nombre_contacto = request.form.get("nombre_contacto")
        telefono_contacto = request.form.get("telefono_contacto")
        parentesco = request.form.get("parentesco")
        
        
        if nombre_contacto and telefono_contacto and parentesco:
            nuevo_contacto = ContactoEmergencia(
                nombre_contacto=nombre_contacto,
                telefono=telefono_contacto,
                parentesco=parentesco
            )
            nuevo_jugador.contacto_emergencia = nuevo_contacto

        db.session.add(nuevo_jugador)
        db.session.commit()
        return redirect(url_for('admin.vista_jugadores_admin'))

    return render_template("admin/form_jugador.html")


# Editar jugador
#
@admin_bp.route("/jugadores/editar/<int:id>", methods=["GET", "POST"])
def editar_jugador(id):
    jugador = db.session.get(Jugador, id)
    if request.method == "POST":
        # Actualizar datos del Jugador
        jugador.nombre = request.form.get("nombre")
        jugador.apellido_paterno = request.form.get("apellido_paterno")
        jugador.apellido_materno = request.form.get("apellido_materno")
        
        from datetime import datetime
        f_nac_str = request.form.get("fecha_nacimiento")
        jugador.fecha_nacimiento = datetime.strptime(f_nac_str, "%Y-%m-%d").date() if f_nac_str else None
        jugador.sexo = request.form.get("sexo")
        
        # Actualizar o Crear Contacto de Emergencia
        nombre_contacto = request.form.get("nombre_contacto")
        telefono_contacto = request.form.get("telefono_contacto")
        parentesco = request.form.get("parentesco")
        
        if jugador.contacto_emergencia:
            jugador.contacto_emergencia.nombre_contacto = nombre_contacto
            jugador.contacto_emergencia.telefono = telefono_contacto
            jugador.contacto_emergencia.parentesco = parentesco
        elif nombre_contacto and telefono_contacto and parentesco:
            nuevo_contacto = ContactoEmergencia(
                nombre_contacto=nombre_contacto,
                telefono=telefono_contacto,
                parentesco=parentesco
            )
            jugador.contacto_emergencia = nuevo_contacto
        
        db.session.commit()
        return redirect(url_for('admin.vista_jugadores_admin'))
        
    return render_template("admin/editar_jugador.html", jugador=jugador)

# Eliminar player
@admin_bp.route("/jugadores/eliminar/<int:id>")
def eliminar_jugador(id):
    jugador = db.session.get(Jugador, id)
    if jugador:
        db.session.delete(jugador)
        db.session.commit()
    return redirect(url_for('admin.vista_jugadores_admin'))

# ==========================================
# Todo lo de inscripciones
# ==========================================

@admin_bp.route("/inscripciones")
def vista_inscripciones_admin():
    # Jalamos todas las inscripciones
    inscripciones_db = db.session.execute(db.select(Inscripcion)).scalars().all()
    return render_template("admin/inscripciones_admin.html", inscripciones=inscripciones_db)

@admin_bp.route("/inscripciones/nueva", methods=["GET", "POST"])
def crear_inscripcion():
    if request.method == "POST":
        torneo_id = request.form.get("torneo_id")
        equipo_id = request.form.get("equipo_id")
        estado = request.form.get("estado_inscripcion")

        nueva_inscripcion = Inscripcion(
            torneo_id=torneo_id,
            equipo_id=equipo_id,
            estado_inscripcion=estado
        )
        db.session.add(nueva_inscripcion)
        db.session.commit()
        return redirect(url_for('admin.vista_inscripciones_admin'))

    # Para el formulario necesitamos la lista de torneos y equipos activos
    torneos = db.session.execute(db.select(Torneo).where(Torneo.activo==True)).scalars().all()
    equipos = db.session.execute(db.select(Equipo).where(Equipo.activo==True)).scalars().all()
    return render_template("admin/form_inscripcion.html", torneos=torneos, equipos=equipos)

@admin_bp.route("/inscripciones/editar/<int:id>", methods=["GET", "POST"])
def editar_inscripcion(id):
    inscripcion = db.session.get(Inscripcion, id)
    if request.method == "POST":
        
        inscripcion.estado_inscripcion = request.form.get("estado_inscripcion")
        db.session.commit()
        return redirect(url_for('admin.vista_inscripciones_admin'))
        
    return render_template("admin/editar_inscripcion.html", inscripcion=inscripcion)

@admin_bp.route("/inscripciones/eliminar/<int:id>")
def eliminar_inscripcion(id):
    inscripcion = db.session.get(Inscripcion, id)
    if inscripcion:
        db.session.delete(inscripcion)
        db.session.commit()
    return redirect(url_for('admin.vista_inscripciones_admin'))


# ==========================================
# ROSTER POR INSCRIPCIÓN (Plantilla del equipo en el torneo)
# ==========================================

@admin_bp.route("/inscripciones/<int:id>/roster", methods=["GET", "POST"])
def roster_inscripcion(id):
    # Jalamos la inscripción específica (Ej: Halcones en Apertura 2026)
    inscripcion = db.session.get(Inscripcion, id)
    
    if request.method == "POST":
        jugador_id = request.form.get("jugador_id")
        dorsal = request.form.get("dorsal")
        es_capitan = True if request.form.get("es_capitan") else False
        
        nuevo_registro = RegistroJugador(
            inscripcion_id=inscripcion.id,
            jugador_id=jugador_id,
            dorsal=dorsal,
            es_capitan=es_capitan
        )
        db.session.add(nuevo_registro)
        db.session.commit()
        return redirect(url_for('admin.roster_inscripcion', id=inscripcion.id))
        
    # Buscar que jugadores ya están registrados en esta inscripción para no repetirlos
    jugadores_registrados = [registro.jugador_id for registro in inscripcion.roster_jugadores]
    
    if jugadores_registrados:
        jugadores_disponibles = db.session.execute(
            db.select(Jugador).where(Jugador.id.notin_(jugadores_registrados))
        ).scalars().all()
    else:
        jugadores_disponibles = db.session.execute(db.select(Jugador)).scalars().all()
    
    return render_template("admin/roster_inscripcion.html", inscripcion=inscripcion, jugadores_disponibles=jugadores_disponibles)

@admin_bp.route("/inscripciones/quitar_jugador/<int:registro_id>")
def quitar_jugador_inscripcion(registro_id):
    registro = db.session.get(RegistroJugador, registro_id)
    if registro:
        insc_id = registro.inscripcion_id
        db.session.delete(registro)
        db.session.commit()
        return redirect(url_for('admin.roster_inscripcion', id=insc_id))
    return redirect(url_for('admin.vista_inscripciones_admin'))


# ==========================================
# MÓDULO DE ÁRBITROS
# ==========================================

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
        return redirect(url_for('admin.vista_arbitros_admin'))
        
    return render_template("admin/editar_arbitro.html", arbitro=arbitro)

@admin_bp.route("/arbitros/eliminar/<int:id>")
def eliminar_arbitro(id):
    arbitro = db.session.get(Arbitro, id)
    if arbitro:
        db.session.delete(arbitro)
        db.session.commit()
    return redirect(url_for('admin.vista_arbitros_admin'))