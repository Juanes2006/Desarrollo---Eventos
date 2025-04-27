from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Criterio, Calificacion, Instrumento, Participantes, ParticipantesEventos, Evento
from flask_sqlalchemy import SQLAlchemy
from app import db
from . import evaluadores_bp

@evaluadores_bp.route('/panel/<int:evento_id>', methods=['GET'])
def panel_evaluador(evento_id):
    return render_template('evaluadores/evaluador_base.html', evento_id=evento_id)

@evaluadores_bp.route('/seleccionar_evento', methods=['GET'])
def seleccionar_evento():
    # Aquí deberías traer los eventos en los que el usuario es evaluador
    eventos = Evento.query.all()  # o solo eventos activos para evaluar
    return render_template('evaluadores/seleccionar_evento.html', eventos=eventos)


# HU44: Cargar instrumentos
@evaluadores_bp.route('/instrumento/<int:evento_id>')
def ver_instrumento(evento_id):
    instrumento = Instrumento.query.filter_by(inst_evento_fk=evento_id).first()
    criterios = Criterio.query.filter_by(cri_evento_fk=evento_id).all()
    return render_template('evaluadores/instrumento.html', instrumento=instrumento, criterios=criterios, evento_id=evento_id)

# HU45: Calificar participante
@evaluadores_bp.route('/calificar/<string:participante_id>', methods=['GET', 'POST'])
def calificar_participante(participante_id):
    criterios = Criterio.query.all()
    if request.method == 'POST':
        for criterio in criterios:
            calificacion = request.form.get(str(criterio.cri_id))
            if calificacion:
                nueva_calificacion = Calificacion(
                    cal_evaluador_fk='EVALUADOR_ID',  # <-- debes pasar el id correcto
                    cal_criterio_fk=criterio.cri_id,
                    cal_participante_fk=participante_id,
                    cal_valor=int(calificacion)
                )
                db.session.add(nueva_calificacion)
        db.session.commit()
        flash('Calificaciones guardadas', 'success')
        return redirect(url_for('evaluadores.calificar_participante', participante_id=participante_id))
    return render_template('evaluadores/calificar.html', criterios=criterios, participante_id=participante_id)

# HU46: Tabla de posiciones
@evaluadores_bp.route('/posiciones')
def tabla_posiciones():
    posiciones = db.session.query(
        Calificacion.cal_participante_fk,
        db.func.sum(Calificacion.cal_valor).label('puntaje_total')
    ).group_by(Calificacion.cal_participante_fk).order_by(db.desc('puntaje_total')).all()
    
    return render_template('evaluadores/tabla_posiciones.html', posiciones=posiciones)

# HU47: Calificaciones otorgadas por evaluador
@evaluadores_bp.route('/mis-calificaciones/<string:evaluador_id>')
def mis_calificaciones(evaluador_id):
    calificaciones = Calificacion.query.filter_by(cal_evaluador_fk=evaluador_id).all()
    return render_template('evaluadores/mis_calificaciones.html', calificaciones=calificaciones)

# Listar y crear criterios
@evaluadores_bp.route('/criterios', methods=['GET', 'POST'])
def gestionar_criterios_evaluador():
    if request.method == 'POST':
        descripcion = request.form.get('descripcion')
        peso = request.form.get('peso')
        evento_id = request.form.get('evento_id')
        
        if descripcion and peso and evento_id:
            nuevo_criterio = Criterio(
                cri_descripcion=descripcion,
                cri_peso=peso,
                cri_evento_fk=evento_id
            )
            db.session.add(nuevo_criterio)
            db.session.commit()
            flash('Criterio agregado correctamente', 'success')
        else:
            flash('Faltan datos para agregar el criterio', 'danger')
        
        return redirect(url_for('evaluadores.gestionar_criterios_evaluador'))
    
    criterios = Criterio.query.all()
    return render_template('evaluadores/criterios.html', criterios=criterios)

# Editar criterio
@evaluadores_bp.route('/criterios/<int:criterio_id>/editar', methods=['GET', 'POST'])
def editar_criterio_evaluador(criterio_id):
    criterio = Criterio.query.get_or_404(criterio_id)
    if request.method == 'POST':
        criterio.cri_descripcion = request.form.get('descripcion')
        criterio.cri_peso = request.form.get('peso')
        criterio.cri_evento_fk = request.form.get('evento_id')
        db.session.commit()
        flash('Criterio actualizado correctamente', 'success')
        return redirect(url_for('evaluadores.gestionar_criterios_evaluador'))
    return render_template('evaluadores/editar_criterio.html', criterio=criterio)

# Eliminar criterio
@evaluadores_bp.route('/criterios/<int:criterio_id>/eliminar', methods=['POST'])
def eliminar_criterio_evaluador(criterio_id):
    criterio = Criterio.query.get_or_404(criterio_id)
    db.session.delete(criterio)
    db.session.commit()
    flash('Criterio eliminado correctamente', 'success')
    return redirect(url_for('evaluadores.gestionar_criterios_evaluador'))

# Para evaluador
@evaluadores_bp.route('/calificaciones/<int:participante_id>')
def ver_calificaciones_evaluador(participante_id):
    calificaciones = Calificacion.query.filter_by(cal_participante_fk=participante_id).all()
    participante = Participantes.query.get_or_404(participante_id)
    return render_template('evaluadores/ver_calificaciones.html', calificaciones=calificaciones, participante=participante)
