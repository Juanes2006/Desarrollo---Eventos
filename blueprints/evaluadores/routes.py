from flask import Blueprint, current_app,   render_template, request, redirect, url_for, flash, session
from models import Criterio, Calificacion, Instrumento, Participantes, ParticipantesEventos, Evento, Evaluador, evaluador_evento
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc
from app import db
from . import evaluadores_bp

@evaluadores_bp.route('/evaluador/<string:eva_id>/evento/<int:evento_id>/panel')
def panel_evaluador(eva_id, evento_id):
    """
    Vista para el panel del evaluador donde se gestionan los participantes y calificaciones.
    """
    # Obtiene el evaluador por su ID
    evaluador = Evaluador.query.get_or_404(eva_id)
    
    # Obtiene el evento por su ID
    evento = Evento.query.get_or_404(evento_id)

    # Obtiene los participantes aceptados para el evento
    participantes_eventos = ParticipantesEventos.query.filter_by(
        par_eve_evento_fk=evento_id,
        par_estado='ACEPTADO'
    ).all()

    # Extrae los participantes desde la relación
    participantes = [pe.participante for pe in participantes_eventos]

    # Renderiza la plantilla del panel del evaluador con los datos necesarios
    return render_template('evaluadores/panel_evaluador.html',
                           evaluador=evaluador,
                           evento=evento,
                           participantes=participantes)


@evaluadores_bp.route('/seleccionar_evento', methods=['GET'])
def seleccionar_evento():
    if 'evaluador_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('evaluadores.iniciosesion'))

    eventos = Evento.query.all()
    evaluador = Evaluador.query.filter_by(eva_id=session['evaluador_id']).first()
    eventos = (
        db.session.query(Evento)
        .join(evaluador_evento, evaluador_evento.c.evento_id == Evento.eve_id)
        .filter(evaluador_evento.c.evaluador_id == evaluador.eva_id)
        .all()
    )
    return render_template('evaluadores/seleccionar_evento.html', eventos=eventos, evaluador=evaluador)




@evaluadores_bp.route('/criterios/<int:evento_id>', methods=['GET', 'POST'])
def gestionar_criterios(evento_id):
    criterios = Criterio.query.filter_by(cri_evento_fk=evento_id).all()
    instrumento = Instrumento.query.filter_by(inst_evento_fk=evento_id).first()
    participantes = db.session.query(Participantes).join(ParticipantesEventos).filter(
        ParticipantesEventos.par_eve_evento_fk == evento_id,
        ParticipantesEventos.par_estado == 'ACEPTADO'  # si quieres sólo aceptados
    ).all()

    if request.method == 'POST':
        accion = request.form.get('accion')

        if accion == 'crear':
            descripcion = request.form.get('descripcion')
            peso = request.form.get('peso')

            nuevo_criterio = Criterio(
                cri_descripcion=descripcion,
                cri_peso=float(peso),
                cri_evento_fk=evento_id
            )
            db.session.add(nuevo_criterio)
            db.session.commit()
            flash('Criterio creado exitosamente.', 'success')

        elif accion == 'editar':
            criterio_id = request.form.get('criterio_id')
            criterio = Criterio.query.get(criterio_id)
            if criterio:
                criterio.cri_descripcion = request.form.get('descripcion')
                criterio.cri_peso = float(request.form.get('peso'))
                db.session.commit()
                flash('Criterio actualizado exitosamente.', 'success')
            else:
                flash('Criterio no encontrado.', 'danger')

        elif accion == 'eliminar':
            criterio_id = request.form.get('criterio_id')
            criterio = Criterio.query.get(criterio_id)
            if criterio:
                db.session.delete(criterio)
                db.session.commit()
                flash('Criterio eliminado exitosamente.', 'success')
            else:
                flash('Criterio no encontrado.', 'danger')

        return redirect(url_for('evaluadores.gestionar_criterios', evento_id=evento_id))

    return render_template('evaluadores/criterios.html', criterios=criterios, evento_id=evento_id , instrumento=instrumento, participantes=participantes)


@evaluadores_bp.route('/evaluador/evento/<int:evento_id>/instrumento', methods=['GET', 'POST'])
def cargar_instrumento(evento_id):
    instrumento_existente = Instrumento.query.filter_by(inst_evento_fk=evento_id).first()

    if request.method == 'POST':
        tipo = request.form['tipo']
        descripcion = request.form['descripcion']

        if instrumento_existente:
            # Actualizar
            instrumento_existente.inst_tipo = tipo
            instrumento_existente.inst_descripcion = descripcion
            db.session.commit()
            flash('Instrumento actualizado exitosamente.', 'success')
        else:
            # Crear
            nuevo_instrumento = Instrumento(
                inst_tipo=tipo,
                inst_descripcion=descripcion,
                inst_evento_fk=evento_id
            )
            db.session.add(nuevo_instrumento)
            db.session.commit()
            flash('Instrumento cargado exitosamente.', 'success')

        return redirect(url_for('evaluadores.cargar_instrumento', evento_id=evento_id))

    return render_template('evaluadores/cargar_instrumento.html', instrumento=instrumento_existente, evento_id=evento_id)


@evaluadores_bp.route('/evaluador/<string:eva_id>/evento/<int:evento_id>/participantes')
def lista_participantes(eva_id, evento_id):
    """
    Muestra la lista de participantes aceptados para el evento.
    """
    # Se buscan las relaciones de participantes que están aceptados en el evento
    participantes_eventos = ParticipantesEventos.query.filter_by(
        par_eve_evento_fk=evento_id,
        par_estado='ACEPTADO'
    ).all()

    # Se extrae la lista real de participantes
    participantes = [pe.participante for pe in participantes_eventos]

    return render_template('evaluadores/lista_participantes.html',
                           eva_id=eva_id,
                           evento_id=evento_id,
                           participantes=participantes)

# 2. Calificar un participante
@evaluadores_bp.route('/evaluador/<string:eva_id>/evento/<int:evento_id>/participante/<string:par_id>/calificar',
                      methods=['GET', 'POST'])
def calificar_participante(eva_id, evento_id, par_id):
    """
    GET: Muestra el formulario de calificación con los criterios del evento.
    POST: Guarda (o actualiza) las calificaciones ingresadas por el evaluador para cada criterio.
    """
    # Se valida la existencia de evaluador, evento y participante
    evaluador = Evaluador.query.get_or_404(eva_id)
    evento = Evento.query.get_or_404(evento_id)
    participante = Participantes.query.get_or_404(par_id)

    # Se obtienen todos los criterios vinculados al evento
    criterios = Criterio.query.filter_by(cri_evento_fk=evento_id).all()

    if request.method == 'POST':
        # Recorremos cada criterio para procesar la calificación
        for criterio in criterios:
            # El nombre del input en el formulario debe ser 'criterio_{{ criterio.cri_id }}'
            field_name = f'criterio_{criterio.cri_id}'
            if field_name in request.form:
                try:
                    valor = int(request.form[field_name])
                except ValueError:
                    flash(f"El valor para el criterio {criterio.cri_descripcion} debe ser numérico.", "danger")
                    continue

                # Revisamos si ya existe una calificación para este evaluador/criterio/participante
                calificacion = Calificacion.query.filter_by(
                    cal_evaluador_fk=evaluador.eva_id,
                    cal_criterio_fk=criterio.cri_id,
                    cal_participante_fk=participante.par_id
                ).first()

                if calificacion:
                    # Actualizar la calificación existente
                    calificacion.cal_valor = valor
                else:
                    # Crear una nueva calificación
                    nueva_calificacion = Calificacion(
                        cal_evaluador_fk=evaluador.eva_id,
                        cal_criterio_fk=criterio.cri_id,
                        cal_participante_fk=participante.par_id,
                        cal_valor=valor
                    )
                    db.session.add(nueva_calificacion)
        db.session.commit()
        flash("Calificaciones guardadas correctamente.", "success")
        return redirect(url_for('evaluadores.calificar_participante',
                                eva_id=evaluador.eva_id,
                                evento_id=evento.eve_id,
                                par_id=participante.par_id))

    # Si es GET, se cargan las calificaciones ya guardadas (si existieran) para precargar el formulario
    existing = {
        cal.cal_criterio_fk: cal.cal_valor
        for cal in Calificacion.query.filter_by(
            cal_evaluador_fk=evaluador.eva_id,
            cal_participante_fk=participante.par_id
        ).all()
    }

    return render_template('evaluadores/calificar.html',
                           evaluador=evaluador,
                           evento=evento,
                           participante=participante,
                           criterios=criterios,
                           existing=existing)
    
    
    
@evaluadores_bp.route('/evaluador/<string:eva_id>/evento/<int:evento_id>/ranking')
def ver_ranking(eva_id, evento_id):
    """
    Muestra el ranking (tabla de posiciones) de todos los participantes 
    en el evento, calculando la suma ponderada de sus calificaciones.
    Solo debería accederse si el evaluador (eva_id) tiene permiso sobre el evento.
    """

    # 1. Verificar la existencia del evaluador y evento (opcional, según tu control)
    evaluador = Evaluador.query.get_or_404(eva_id)
    evento = Evento.query.get_or_404(evento_id)
    # Opcional: Verificar si 'eva_id' está realmente asignado a ese evento (depende de tu modelo).

    # 2. Hacer la consulta para obtener la calificación total (suma ponderada) 
    #    de cada participante en este evento.
    ranking = (
        db.session.query(
            Participantes.par_id.label('participante_id'),
            Participantes.par_nombre.label('participante_nombre'),
            func.sum(Calificacion.cal_valor * Criterio.cri_peso).label('puntaje_total')
        )
        .join(Calificacion, Calificacion.cal_participante_fk == Participantes.par_id)
        .join(Criterio, Criterio.cri_id == Calificacion.cal_criterio_fk)
        .join(Evento, Evento.eve_id == Criterio.cri_evento_fk)
        .filter(Evento.eve_id == evento_id)
        .group_by(Participantes.par_id)
        .order_by(desc('puntaje_total'))  # Orden desc para que el primero tenga el mayor puntaje
    ).all()

    # 3. Renderizar la plantilla, enviando el ranking
    return render_template('evaluadores/ranking.html',
                           evaluador=evaluador,
                           evento=evento,
                           ranking=ranking)
    
    
    
@evaluadores_bp.route('/login', methods=['GET', 'POST'])
def iniciosesion():
    if request.method == 'POST':
        eva_id = request.form.get('eva_id')  # o correo, dependiendo cómo quieras identificarlo

        evaluador = Evaluador.query.filter_by(eva_id=eva_id).first()
        
        if evaluador:
            session['evaluador_id'] = evaluador.eva_id  # Guardamos en sesión
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('evaluadores.seleccionar_evento'))
        else:
            flash('Evaluador no encontrado, verifica tus datos', 'danger')
            return redirect(url_for('evaluadores.iniciosesion'))

    return render_template('evaluadores/inicio_de_sesion.html')

@evaluadores_bp.route('/cerrar_sesion', methods=['POST'])
def cerrar_sesion():
    session.pop('evaluador_id', None)  # Elimina el evaluador de la sesión
    flash('Sesión cerrada exitosamente.', 'success')
    return redirect(url_for('evaluadores.iniciosesion'))  # Redirige al login
