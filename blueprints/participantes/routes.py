from flask import render_template, request, redirect, url_for, flash, current_app
from . import participantes_bp
from models import db, Participantes, ParticipantesEventos, Evento
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
            return redirect(url_for('verificar_participante'))

        # Si el participante existe, lo enviamos a la vista de modificación
        return redirect(url_for('modificar_participante', user_id=par_id))

    return render_template('verificar_participante.html')

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

@participantes_bp.route('/mi_info', methods=['GET','POST'])
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
                    eventos_inscritos.append({
                        'eve_id': inscripcion[0],
                        'eve_nombre': inscripcion[1],
                        'eve_fecha_inicio': inscripcion[2],
                        'eve_ciudad': inscripcion[3],
                        'par_estado': inscripcion[4],
                        'par_eve_documentos': inscripcion[5]
                    })
            else:
                flash("No se encontró información para el ID proporcionado.", "danger")

    return render_template("participantes/par_informacion.html", 
                           titulo="Mis Eventos Inscritos", 
                           participante=participante, 
                           eventos_inscritos=eventos_inscritos)
