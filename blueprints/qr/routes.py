from flask import render_template, request, redirect, url_for, flash, send_file,make_response
from . import qr_bp
from models import Evento, AsistentesEventos, ParticipantesEventos, Asistentes, Participantes
import segno, base64
from io import BytesIO
from datetime import datetime

@qr_bp.route('/consulta_qr', methods=['GET','POST'])
def consulta_qr():
    events = Evento.query.all()

    if request.method == 'POST':
        event_id = request.form.get('event_id')
        user_id = request.form.get('user_id')

        if not event_id or not user_id:
            flash("Debes seleccionar un evento y escribir tu documento.", "warning")
            return redirect(url_for('consulta_qr'))

        # Intentar buscar el usuario en ambas tablas (Asistentes y Participantes)
        usuario = Asistentes.query.get(user_id) or Participantes.query.get(user_id)
        tipo = 'asistente' if Asistentes.query.get(user_id) else 'participante' if Participantes.query.get(user_id) else None

        if usuario:
            flash("Usuario encontrado", "success")
        else:
            flash("Usuario no encontrado", "danger")

        return redirect(url_for('qr.mostrar_qr', event_id=event_id, user_id=user_id))

    return render_template('qr/consulta_qr.html', events=events)


@qr_bp.route('/mostrar_qr/<int:event_id>/<string:user_id>')
def mostrar_qr(event_id, user_id):
    # Verificar si el usuario es asistente o participante
    asistente_evento = AsistentesEventos.query.filter_by(
        asi_eve_asistente_fk=user_id,
        asi_eve_evento_fk=event_id
    ).first()
    
    participante_evento = None
    if not asistente_evento:
        participante_evento = ParticipantesEventos.query.filter_by(
            par_eve_participante_fk=user_id,
            par_eve_evento_fk=event_id
        ).first()
    
    # Si no es ni asistente ni participante, redirigir
    if not asistente_evento and not participante_evento:
        flash("No estás registrado como Asistente ni Participante en este evento.", "danger")
        return redirect(url_for('qr.consulta_qr'))
    
    # ✅ Verificar si el participante fue aceptado
    if participante_evento and participante_evento.par_estado != "ACEPTADO":
        flash("Tu inscripción aún no ha sido aceptada. No puedes obtener el QR.", "danger")
        return redirect(url_for('qr.consulta_qr'))

    # ✅ Verificar si el asistente fue aceptado (si aplica)
    if asistente_evento and asistente_evento.asi_eve_estado != "ACEPTADO":
        flash("Tu asistencia aún no ha sido confirmada. No puedes obtener el QR.", "danger")
        return redirect(url_for('qr.consulta_qr'))

    # Determinar el tipo de usuario
    if asistente_evento:
        qr_data = f"Tipo=Asistente|ID={user_id}|Evento={event_id}|Clave={asistente_evento.asi_eve_clave}"
        registration_type = "Asistente"
        user_document = asistente_evento.asi_eve_asistente_fk
    else:
        qr_data = f"Tipo=Participante|ID={user_id}|Evento={event_id}|Clave={participante_evento.par_eve_clave}"
        registration_type = "Participante"
        user_document = participante_evento.par_eve_participante_fk

    # Generar el QR
    qr = segno.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=5)
    qr_bytes = buffer.getvalue()
    qr_b64 = base64.b64encode(qr_bytes).decode('utf-8')
    
    # Obtener el evento
    evento = Evento.query.get(event_id)
    if not evento:
        flash("El evento no fue encontrado.", "danger")
        return redirect(url_for('qr.consulta_qr'))
    
    return render_template(
        'mostrar_qr.html',
        qr_image=qr_b64,
        evento=evento,  
        registration_type=registration_type,
        user_document=user_document,
        user_id=user_id
    )
    
@qr_bp.route('/descargar_qr/<int:event_id>/<string:user_id>')
def descargar_qr(event_id, user_id):
    asistente_evento = AsistentesEventos.query.filter_by(
        asi_eve_asistente_fk=user_id,
        asi_eve_evento_fk=event_id
    ).first()
    participante_evento = None
    if not asistente_evento:
        participante_evento = ParticipantesEventos.query.filter_by(
            par_eve_participante_fk=user_id,
            par_eve_evento_fk=event_id
        ).first()
    if not asistente_evento and not participante_evento:
        return make_response("No estás registrado en este evento.", 404)
    
    if asistente_evento:
        qr_data = f"Tipo=Asistente|ID={user_id}|Evento={event_id}|Clave={asistente_evento.asi_eve_clave}"
    else:
        qr_data = f"Tipo=Participante|ID={user_id}|Evento={event_id}|Clave={participante_evento.par_eve_clave}"
    
    qr = segno.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=5)
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name='qr_code.png')


