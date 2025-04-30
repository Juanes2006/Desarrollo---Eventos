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
        return redirect(url_for('evaluadores.login_evaluador'))

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
    # Consulta los criterios actuales y el instrumento
    evento = Evento.query.get_or_404(evento_id)
    criterios = Criterio.query.filter_by(cri_evento_fk=evento_id).all()
    instrumento = Instrumento.query.filter_by(inst_evento_fk=evento_id).first()
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        peso_str = request.form.get('peso')

        # Convertir el peso a número flotante, en caso de error, mostrar mensaje y redirigir.
        try:
            peso = float(peso_str) if peso_str else 0
        except ValueError:
            flash('El peso ingresado no es válido.', 'danger')
            return redirect(url_for('admin.gestionar_criterios_admin', evento_id=evento_id))

        if accion == 'crear':
            descripcion = request.form.get('descripcion')
            # Se consulta la suma actual de pesos directamente desde la base de datos.
            suma_actual = db.session.query(db.func.sum(Criterio.cri_peso)).filter_by(cri_evento_fk=evento_id).scalar() or 0

            # Si al agregar el nuevo peso se superaría el 100%, se muestra el error y se redirige.
            if suma_actual + peso > 100:
                flash(f'Error: La suma de los porcentajes no puede superar el 100% (actual: {suma_actual}%, intento agregar: {peso}%).', 'danger')
                flash(f'Por favor, ajuste el peso del nuevo criterio, queda por agregar un {100 - suma_actual}%.', 'danger')

                return redirect(url_for('admin.gestionar_criterios_admin', evento_id=evento_id))
            else:
                nuevo_criterio = Criterio(
                    cri_descripcion=descripcion,
                    cri_peso=peso,
                    cri_evento_fk=evento_id
                )
                db.session.add(nuevo_criterio)
                db.session.commit()
                flash('Criterio creado exitosamente.', 'success')

        elif accion == 'editar':
            criterio_id = request.form.get('criterio_id')
            criterio = Criterio.query.get(criterio_id)

            if criterio:
                # Se calcula la suma de los pesos excluyendo el criterio que se pretende actualizar.
                suma_sin_este = db.session.query(db.func.sum(Criterio.cri_peso)).filter(
                    Criterio.cri_evento_fk == evento_id,
                    Criterio.cri_id != criterio.cri_id
                ).scalar() or 0

                if suma_sin_este + peso > 100:
                    flash(f'Error: La suma de los porcentajes no puede superar el 100% (actual sin este: {suma_sin_este}%, intento editar a: {peso}%).', 'danger')
                    return redirect(url_for('admin.gestionar_criterios_admin', evento_id=evento_id))
                else:
                    criterio.cri_descripcion = request.form.get('descripcion')
                    criterio.cri_peso = peso
                    db.session.commit()
                    flash('Criterio actualizado exitosamente.', 'success')
            else:
                flash('Criterio no encontrado.', 'danger')

        elif accion == 'eliminar':
            criterio_id = request.form.get('criterio_id')
            criterio = Criterio.query.get(criterio_id)

            if criterio:
                calificaciones_vinculadas = Calificacion.query.filter_by(cal_criterio_fk=criterio_id).count()
                if calificaciones_vinculadas > 0:
                    flash(
                        f'No se puede eliminar el criterio "{criterio.cri_descripcion}" porque tiene {calificaciones_vinculadas} calificación(es) asociada(s).',
                        'danger'
                    )
                else:
                    db.session.delete(criterio)
                    db.session.commit()
                    flash('Criterio eliminado exitosamente.', 'success')
            else:
                flash('Criterio no encontrado.', 'danger')

        return redirect(url_for('admin.gestionar_criterios_admin', evento_id=evento_id, ))

    # GET method: se calcula el total de peso asignado
    total_peso = db.session.query(db.func.sum(Criterio.cri_peso)).filter_by(cri_evento_fk=evento_id).scalar() or 0

    return render_template(
        'evaluadores/criterios.html',
        criterios=criterios,
        instrumento=instrumento,
        evento_id=evento_id,
        total_peso=round(total_peso, 2),
        evento=evento
    )

    # Verificación del total actual para mostrar feedback
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
def login_evaluador():
    if request.method == 'POST':
        eva_id = request.form.get('eva_id')  # o correo, dependiendo cómo quieras identificarlo

        evaluador = Evaluador.query.filter_by(eva_id=eva_id).first()
        
        if evaluador:
            session['evaluador_id'] = evaluador.eva_id  # Guardamos en sesión
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('evaluadores.seleccionar_evento'))
        else:
            flash('Evaluador no encontrado, verifica tus datos', 'danger')
            return redirect(url_for('evaluadores.login_evaluador'))

    return render_template('evaluadores/login.html')

@evaluadores_bp.route('/logout',  methods=['GET', 'POST'])
def logout_evaluador():
    session.pop('evaluador_id', None)  # Elimina el evaluador de la sesión
    flash('Sesión cerrada exitosamente.', 'success')
    return redirect(url_for('evaluadores.login_evaluador'))  # Redirige al login

from collections import defaultdict

@evaluadores_bp.route('/evaluador/evento/<int:evento_id>/calificaciones')
def ver_calificaciones_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    # Consulta los participantes que tengan calificaciones asociadas a criterios del evento
    participantes_calificados = (
        db.session.query(Participantes)
        .join(Calificacion, Calificacion.cal_participante_fk == Participantes.par_id)
        .join(Criterio, Criterio.cri_id == Calificacion.cal_criterio_fk)
        .filter(Criterio.cri_evento_fk == evento_id)
        .distinct()
        .all()
    )

    return render_template(
        'evaluadores/ver_calificaciones.html',
        evento=evento,
        participantes=participantes_calificados
    )
    
@evaluadores_bp.route('/evento/<int:evento_id>/calificaciones/participante/<int:participante_id>')
def ver_calificaciones_participante(evento_id, participante_id):
    evento = Evento.query.get_or_404(evento_id)
    participante = Participantes.query.get_or_404(participante_id)

    # Consulta las calificaciones de este participante para el evento seleccionado
    calificaciones = (
        db.session.query(
            Criterio.cri_descripcion,
            Evaluador.eva_nombre,
            Calificacion.cal_valor
        )
        .join(Calificacion, Calificacion.cal_criterio_fk == Criterio.cri_id)
        .join(Evaluador, Evaluador.eva_id == Calificacion.cal_evaluador_fk)
        .filter(
            Criterio.cri_evento_fk == evento_id,
            Calificacion.cal_participante_fk == participante_id
        )
        .all()
    )

    return render_template(
        'evaluadores/calificaciones_participante.html',
        evento=evento,
        participante=participante,
        calificaciones=calificaciones
    )