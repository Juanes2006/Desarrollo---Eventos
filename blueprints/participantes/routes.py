from flask import render_template, request, redirect, url_for, flash, current_app
from . import participantes_bp
from models import db, Participantes,Instrumento ,Evaluador,  ParticipantesEventos, Evento, Criterio, Calificacion
from utilities.files import save_file


@participantes_bp.route('/verificar', methods=['GET','POST'])
def verificar_participante():
    if request.method == 'POST':
        par_id = request.form.get('par_id')

        if not par_id:
            flash("Por favor, ingresa tu ID de participante.", "warning")
            return redirect(url_for('verificar_participante'))

        participante = Participantes.query.get(par_id)

        if not participante:
            flash("No se encontró un participante con este ID.", "danger")
            return redirect(url_for('participantes.verificar_participante'))

        # Si el participante existe, lo enviamos a la vista de modificación
        return redirect(url_for('participantes.modificar_participante', user_id=par_id))

    return render_template('participantes/verificar_participante.html')

@participantes_bp.route('/modificar/<string:user_id>/<int:evento_id>', methods=['GET','POST'])
def modificar_participante(user_id, evento_id):
    participante = Participantes.query.get(user_id)

    if not participante:
        flash("Participante no encontrado", "danger")
        return redirect(url_for('consulta_qr'))

    # Buscar la inscripción del participante a ese evento
    evento_participante = ParticipantesEventos.query.filter_by(
        par_eve_participante_fk=user_id,
        par_eve_evento_fk=evento_id
    ).first()

    # Obtener el evento para mostrar su nombre
    evento = Evento.query.get(evento_id)

    if not evento_participante or not evento:
        flash("No se encontró la inscripción o el evento", "danger")
        return redirect(url_for('consulta_qr'))

    if request.method == 'POST':
        participante.par_nombre = request.form['nombre']
        participante.par_correo = request.form['correo']
        participante.par_telefono = request.form['telefono']

        if 'documento' in request.files:
            file = request.files['documento']
            if file and file.filename != '':
                filename = save_file(
    file,
    current_app.config['UPLOAD_FOLDER_PAGOS'],
    current_app.config['ALLOWED_EXTENSIONS_PAGOS']
)

                if filename:
                    evento_participante.par_eve_documentos = filename
                else:
                    flash("Extensión no permitida o error al guardar el archivo", "warning")

        db.session.commit()
        flash("Información actualizada con éxito", "success")
        return redirect(url_for('participantes.mi_info'))

    return render_template(
        'participantes/modificar_participante.html',
        participante=participante,
        evento_participante=evento_participante,
        evento_nombre=evento.eve_nombre
    )

from sqlalchemy import func

@participantes_bp.route('/mi_info', methods=['GET', 'POST'])
def mi_info():
    participante = None
    eventos_inscritos = []
   

    if request.method == "POST":
        par_id = request.form.get("par_id")

        if par_id:
            participante = Participantes.query.filter_by(par_id=par_id).first()

            if participante:
                inscripciones = db.session.query(
                    Evento.eve_id,
                    Evento.eve_nombre,
                    Evento.eve_fecha_inicio,
                    Evento.eve_ciudad,
                    ParticipantesEventos.par_estado,
                    ParticipantesEventos.par_eve_documentos
                ).join(ParticipantesEventos, Evento.eve_id == ParticipantesEventos.par_eve_evento_fk)\
                 .filter(ParticipantesEventos.par_eve_participante_fk == par_id, Evento.eve_estado == "ACTIVO")\
                 .all()

                for inscripcion in inscripciones:
                    eve_id = inscripcion[0]

                    # 🔥 1. Puntaje total del participante en este evento
                    puntaje_total = db.session.query(func.sum(Calificacion.cal_valor))\
                        .join(Criterio, Calificacion.cal_criterio_fk == Criterio.cri_id)\
                        .filter(Calificacion.cal_participante_fk == par_id,
                                Criterio.cri_evento_fk == eve_id)\
                        .scalar() or 0

                    # 🔥 2. Ranking general de los participantes en ese evento
                    participantes_puntajes = db.session.query(
                        Calificacion.cal_participante_fk,
                        func.sum(Calificacion.cal_valor).label('total_puntaje')
                    ).join(Criterio, Calificacion.cal_criterio_fk == Criterio.cri_id)\
                     .filter(Criterio.cri_evento_fk == eve_id)\
                     .group_by(Calificacion.cal_participante_fk)\
                     .order_by(func.sum(Calificacion.cal_valor).desc())\
                     .all()

                    posicion = None
                    for idx, (part_id, total_puntaje) in enumerate(participantes_puntajes, start=1):
                        if str(part_id) == str(par_id):
                            posicion = idx
                            break
                    
                    # 🔥 3. Instrumento relacionado
                    # 🔥 3. Instrumento relacionado
                    instrumento = Instrumento.query.filter_by(inst_evento_fk=eve_id).first()
                    criterios = Criterio.query.filter_by(cri_evento_fk=eve_id).all()


                    

                    eventos_inscritos.append({
                        'evento': {
                            'eve_id': eve_id,
                            'eve_nombre': inscripcion[1],
                            'eve_fecha_inicio': inscripcion[2],
                            'eve_ciudad': inscripcion[3],
                        },
                        'par_estado': inscripcion[4],
                        'par_eve_documentos': inscripcion[5],
                        'puntaje_total': puntaje_total,
                        'posicion': posicion,
                        'instrumento': instrumento,
                        'criterios': criterios # ⬅️ AÑADIMOS ESTO
                    })
                    print("Evento ID en consulta:", eve_id)

            else:
                flash("No se encontró información para el ID proporcionado.", "danger")

    return render_template("participantes/par_informacion.html", 
                           titulo="Mis Eventos Inscritos", 
                           participante=participante,
                           eventos_inscritos=eventos_inscritos)


@participantes_bp.route('/instrumento/<int:evento_id>')
def ver_instrumento(evento_id):
    # Filtra los criterios asociados al evento
    criterios = Criterio.query.filter_by(cri_evento_fk=evento_id).all()
    # Renderiza una vista especial para participantes
    return render_template('participantes/instrumento.html', criterios=criterios)


@participantes_bp.route('/calificaciones/<string:participante_id>')
def ver_calificaciones(participante_id):
    # Consulta todas las calificaciones del participante
    calificaciones = Calificacion.query.filter_by(cal_participante_fk=participante_id).all()
    
    # Calcula el puntaje total sumando cada calificación
    puntaje_total = sum([cal.cal_valor for cal in calificaciones])
    
    #recomendaciones
    # Aquí puedes agregar lógica para recuperar observaciones si las tienes
    #recuperar_observaciones = lambda id: db.session.query(Observacion).filter_by(cal_participante_fk=id).all()
    # Si tienes un modelo de Observacion, puedes descomentar la siguiente línea
    # Por ejemplo: observaciones = recuperar_observaciones(participante_id)
    
    return render_template('participantes/calificaciones.html',
                           calificaciones=calificaciones,
                           puntaje_total=puntaje_total)
    
    
    # Dentro de tu participantes_bp (o donde gestiones rutas para participantes)
@participantes_bp.route('/ranking/<int:evento_id>')
def ranking_participantes(evento_id):
    participantes = Participantes.query.filter_by(par_evento_fk=evento_id).all()
    
    ranking = []

    for participante in participantes:
        # Sumamos los puntajes de cada participante
        puntajes = Calificacion.query.filter_by(cal_participante_fk=participante.par_id).all()
        total_puntaje = sum([p.cal_valor for p in puntajes])
        
        ranking.append({
            'participante': participante,
            'total_puntaje': total_puntaje
        })

    # Ordenamos de mayor a menor puntaje
    ranking.sort(key=lambda x: x['total_puntaje'], reverse=True)

    return render_template('participantes/ranking.html', ranking=ranking)


@participantes_bp.route('/participantes/evento/<int:evento_id>/calificaciones/participante/<int:participante_id>')
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
        'participantes/calificaciones_participante.html',
        evento=evento,
        participante=participante,
        calificaciones=calificaciones
    )  