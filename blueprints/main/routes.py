from flask import render_template, flash, request, redirect, url_for
from . import main_bp
from models import db, Evento
from datetime import datetime
from sqlalchemy.orm import joinedload
from models import Evento, Categoria  



@main_bp.route('/visitante_web/lista_eventos')
def lista_eventos():
    eventos = Evento.query.filter_by(eve_estado="Activo").all()
    return render_template('eventos/lista_eventos.html', titulo="Eventos Activos", eventos=eventos)

@main_bp.route('/')
@main_bp.route('/visitante_web')
def visitante():
    return render_template('participantes/visitante_web.html')

@main_bp.route('/eventos_proximos')
def eventos_proximos():
    eventos = Evento.query.filter_by(eve_estado="ACTIVO").all()
    return render_template('eventos/lista_eventos.html', titulo="Eventos Próximos", eventos=eventos)

@main_bp.route('/visitante_web/buscar_eventos', methods=['GET','POST'])
def buscar_eventos():
    eventos = []
    if request.method == "POST":
        # Recoger los parámetros de búsqueda desde el formulario
        nombre = request.form.get("nombre", "").strip()
        fecha_inicio_str = request.form.get("fecha_inicio", "").strip()
        ciudad = request.form.get("ciudad", "").strip()
        
        # Inicia la consulta base
        query = Evento.query
        
        # Agrega el filtro para el nombre si se ha ingresado
        if nombre:
            query = query.filter(Evento.eve_nombre.contains(nombre))
            
        
        
        # Agrega el filtro para la fecha (ejemplo: eventos que comienzan a partir de una fecha)
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                query = query.filter(Evento.eve_fecha_inicio >= fecha_inicio)
            except ValueError:
                flash("Formato de fecha inválido. Usa AAAA-MM-DD.")
        
        # Agrega el filtro para la ciudad si se ha ingresado
        if ciudad:
            query = query.filter(Evento.eve_ciudad.contains(ciudad))
        
        eventos = query.all()
        flash("Resultados de la búsqueda")
        
    return render_template("participantes/buscar_eventos.html", eventos=eventos)

@main_bp.route('/evento_detalle/<int:eve_id>')
def evento_detalle(eve_id):
    evento = (
        Evento.query
        .filter_by(eve_id=eve_id)
        .options(
            joinedload(Evento.categorias).joinedload(Categoria.area)  # Carga las categorías y áreas
        )
        .first_or_404()
    )
    return render_template('participantes/detalle_evento.html', evento=evento)
