from flask import Blueprint, jsonify, request, render_template
from db import db
from models import Torneo, Equipo, Partido, Anuncio, Cancha

public_bp = Blueprint("public", __name__)


# -----------------------------
# VISTAS HTML
# -----------------------------
@public_bp.get("/")
def index():
    anuncios = Anuncio.query.filter_by(activo=True).order_by(Anuncio.fecha_publicacion.desc()).limit(3).all()
    return render_template("public/index.html", anuncios=anuncios)

@public_bp.get("/torneos")
def pagina_torneos():
    torneos = Torneo.query.filter_by(activo=True).all()
    return render_template("public/torneos.html", torneos=torneos)

@public_bp.get("/equipos")
def pagina_equipos():
    equipos = Equipo.query.filter_by(activo=True).all()
    return render_template("public/equipos.html", equipos=equipos)

@public_bp.get("/partidos")
def pagina_partidos():
    partidos = Partido.query.order_by(Partido.fecha_hora.asc()).all()
    return render_template("public/partidos.html", partidos=partidos)

@public_bp.get("/resultados")
def pagina_resultados():
    resultados = Partido.query.filter_by(estado="finalizado").order_by(Partido.fecha_hora.desc()).all()
    return render_template("public/resultados.html", resultados=resultados)

@public_bp.get("/posiciones")
def pagina_posiciones():
    torneo_id = request.args.get("torneo_id", type=int)
    torneos = Torneo.query.all()
    
    if not torneo_id and torneos:
        torneo_id = torneos[0].id
        
    tabla = []
    if torneo_id:
        # Lógica simplificada para tabla de posiciones
        equipos = Equipo.query.all()
        for e in equipos:
            pj = Partido.query.filter_by(torneo_id=torneo_id, estado="finalizado").filter((Partido.local_id == e.id) | (Partido.visitante_id == e.id)).count()
            
            # Ganados, Empatados, Perdidos
            g = Partido.query.filter_by(torneo_id=torneo_id, estado="finalizado", local_id=e.id).filter(Partido.goles_local > Partido.goles_visitante).count()
            g += Partido.query.filter_by(torneo_id=torneo_id, estado="finalizado", visitante_id=e.id).filter(Partido.goles_visitante > Partido.goles_local).count()
            
            emp = Partido.query.filter_by(torneo_id=torneo_id, estado="finalizado").filter((Partido.local_id == e.id) | (Partido.visitante_id == e.id)).filter(Partido.goles_local == Partido.goles_visitante).count()
            
            p = pj - g - emp
            
            pts = (g * 3) + emp
            
            if pj > 0:
                tabla.append({
                    "equipo": e.nombre,
                    "pj": pj, "g": g, "e": emp, "p": p,
                    "pts": pts
                })
        
        tabla.sort(key=lambda x: x["pts"], reverse=True)

    return render_template("public/posiciones.html", torneos=torneos, tabla=tabla, selected_torneo=torneo_id)

@public_bp.get("/anuncios")
def pagina_anuncios():
    anuncios = Anuncio.query.filter_by(activo=True).order_by(Anuncio.fecha_publicacion.desc()).all()
    return render_template("public/anuncios.html", anuncios=anuncios)

@public_bp.get("/estadisticas")
def pagina_estadisticas():
    return render_template("public/estadisticas.html")

@public_bp.get("/canchas")
def pagina_canchas():
    canchas = Cancha.query.all()
    return render_template("public/canchas.html", canchas=canchas)

@public_bp.get("/login")
def pagina_login():
    return render_template("public/login.html")


# -----------------------------
# API
# -----------------------------
@public_bp.get("/health")
def health():
    return jsonify({
        "ok": True,
        "servicio": "soccerpremier_backend"
    })

@public_bp.get("/api/torneos")
def listar_torneos():
    torneos = Torneo.query.order_by(Torneo.id.desc()).all()
    return jsonify([
        {
            "id": t.id,
            "nombre": t.nombre,
            "categoria": t.categoria,
            "tipo": t.tipo,
            "fecha_inicio": t.fecha_inicio.isoformat() if t.fecha_inicio else None,
            "fecha_fin": t.fecha_fin.isoformat() if t.fecha_fin else None,
            "activo": t.activo
        }
        for t in torneos
    ])

@public_bp.get("/api/equipos")
def listar_equipos():
    equipos = Equipo.query.order_by(Equipo.nombre.asc()).all()
    return jsonify([
        {
            "id": e.id,
            "nombre": e.nombre,
            "representante": e.representante,
            "telefono": e.telefono,
            "logo_url": e.logo_url,
            "activo": e.activo
        }
        for e in equipos
    ])

@public_bp.get("/api/partidos")
def listar_partidos():
    torneo_id = request.args.get("torneo_id", type=int)
    query = Partido.query.order_by(Partido.fecha_hora.asc())
    if torneo_id:
        query = query.filter_by(torneo_id=torneo_id)
    partidos = query.all()
    return jsonify([
        {
            "id": p.id,
            "torneo": p.torneo.nombre,
            "local": p.local.nombre,
            "visitante": p.visitante.nombre,
            "cancha": p.cancha.nombre if p.cancha else "TBD",
            "fecha_hora": p.fecha_hora.strftime("%Y-%m-%d %H:%M"),
            "jornada": p.jornada,
            "estado": p.estado,
            "goles_local": p.goles_local,
            "goles_visitante": p.goles_visitante
        }
        for p in partidos
    ])

@public_bp.get("/api/anuncios")
def listar_anuncios_api():
    anuncios = Anuncio.query.filter_by(activo=True).order_by(Anuncio.fecha_publicacion.desc()).all()
    return jsonify([
        {
            "id": a.id,
            "titulo": a.titulo,
            "contenido": a.contenido,
            "fecha": a.fecha_publicacion.isoformat()
        }
        for a in anuncios
    ])