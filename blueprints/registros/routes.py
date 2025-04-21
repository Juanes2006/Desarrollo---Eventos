from flask import render_template, request, redirect, url_for, flash, current_app
from . import registros_bp
from models import db, Evento, Asistentes, Participantes, AsistentesEventos, ParticipantesEventos
from utilities.files import save_file
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from app4 import app

@registros_bp.route('/<int:evento_id>/registrarme', methods=['GET','POST'])
def registrarme_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    
    if request.method == 'POST':
        tipo = request.form.get('tipo_inscripcion')
        user_id = request.form.get('user_id')
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')
        
        if tipo not in ["Asistente", "Participante"]:
            flash("Por favor, selecciona un tipo de inscripción válido.", "warning")
            return redirect(url_for('registrarme_evento', evento_id=evento_id))
    
        if tipo == "Asistente":
            # Procesa inscripción como Asistente
            asistente = Asistentes.query.get(user_id)
            if not asistente:
                asistente = Asistentes(
                    asi_id=user_id,
                    asi_nombre=nombre,
                    asi_correo=correo,
                    asi_telefono=telefono
                )
                db.session.add(asistente)
    
            soporte_pago = None
            if evento.cobro.lower() in ['sí', 'si'] and 'soporte_pago' in request.files:
                file = request.files['soporte_pago']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    soporte_pago = filename

            clave_asis = user_id[::-1]
            
            registro = AsistentesEventos(
                asi_eve_asistente_fk=user_id,
                asi_eve_evento_fk=evento_id,
                asi_eve_fecha_hora=datetime.utcnow(),
                asi_eve_soporte=soporte_pago,
                asi_eve_estado='Registrado',
                asi_eve_clave=clave_asis
            )
            db.session.add(registro)
    
        elif tipo == "Participante":
            # Procesa inscripción como Participante
            participante = Participantes.query.get(user_id)
            if not participante:
                participante = Participantes(
                    par_id=user_id,
                    par_nombre=nombre,
                    par_correo=correo,
                    par_telefono=telefono
                )
                db.session.add(participante)
    
            documentos = None
            if 'documentos' in request.files:
                file = request.files['documentos']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    documentos = filename
    
            # Generar automáticamente el OR invirtiendo el número de documento (user_id)
            clave_par = user_id[::-1]
    
            registro = ParticipantesEventos(
                par_eve_participante_fk=user_id,
                par_eve_evento_fk=evento_id,
                par_eve_fecha_hora=datetime.utcnow(),
                par_eve_documentos=documentos,
                par_eve_or=clave_par,  
                par_eve_clave=clave_par,
            )
            db.session.add(registro)
    
        db.session.commit()
        flash(f"¡Te has preinscrito exitosamente como {tipo}!", "success")
        return redirect(url_for('main.lista_eventos'))
    
    # Si la solicitud es GET, simplemente renderizamos el formulario
    return render_template('registros/formulario_registro.html', evento=evento)

@registros_bp.route('/cancelar_inscripcion/<int:evento_id>/<string:user_id>', methods=['GET','POST'])
def cancelar_inscripcion(evento_id, user_id):
    def cancelar_inscripcion(evento_id, user_id):
        asistente_evento = AsistentesEventos.query.filter_by(
            asi_eve_asistente_fk=user_id,
            asi_eve_evento_fk=evento_id
        ).first()
        participante_evento = None
        if not asistente_evento:
            participante_evento = ParticipantesEventos.query.filter_by(
                par_eve_participante_fk=user_id,
                par_eve_evento_fk=evento_id
            ).first()
        ##### SI SE LLEGA A ENCONTRAR A ALGUIN INCRITO SEA COMO PARTICIPANTE O ASISTENTE SE BORRA DE LA BD TANTO (ASIS) COMO (ASIS_EVENTOS) TAMBIEN BORRO LOS DOCS DE MI LOCAL
        if asistente_evento:
            db.session.delete(asistente_evento)
            usuario = Asistentes.query.filter_by(asi_id=user_id).first()
            if usuario:
                # Obtener la ruta del archivo de soporte (se asume que es relativa, por ejemplo: "soporte.pdf")
                ruta_archivo = asistente_evento.asi_eve_soporte  
                
                # Si la ruta existe, construir la ruta absoluta
                if ruta_archivo:
                    ruta_archivo = os.path.join(current_app.root_path, 'static', 'uploads', ruta_archivo.strip())
                
                # Eliminar el registro del usuario de la base de datos
                db.session.delete(usuario)
                db.session.commit()
                
                # Intentar eliminar el archivo del sistema
                if ruta_archivo and os.path.exists(ruta_archivo):
                    try:
                        os.remove(ruta_archivo)
                        flash("Archivo de soporte eliminado del sistema.", "success")
                    except Exception as e:
                        flash(f"No se pudo eliminar el archivo de soporte: {str(e)}", "warning")
                else:
                    flash("La ruta del archivo de soporte no existe o es inválida.", "warning")
                
                flash("Inscripción cancelada y usuario eliminado exitosamente.", "success")
                return redirect(url_for('consulta_qr'))

        elif participante_evento:
            db.session.delete(participante_evento)
            usuario = Participantes.query.filter_by(par_id=user_id).first()
            if usuario:
                ruta_documento = participante_evento.par_eve_documentos
                # Si la ruta existe, construir la ruta absoluta
                if ruta_documento:
                    ruta_documento = os.path.join(current_app.root_path, 'static', 'uploads', ruta_documento.strip())
                
                # Eliminar el registro del usuario de la base de datos
                db.session.delete(usuario)
                db.session.commit()
                
                # Intentar eliminar el archivo del sistema
                if ruta_documento and os.path.exists(ruta_documento):
                    try:
                        os.remove(ruta_documento)
                        flash("Archivo de soporte eliminado del sistema.", "success")
                    except Exception as e:
                        flash(f"No se pudo eliminar el archivo de soporte: {str(e)}", "warning")
                else:
                    flash("La ruta del archivo de soporte no existe o es inválida.", "warning")
                
                flash("Inscripción cancelada y usuario eliminado exitosamente.", "success")
                return redirect(url_for('consulta_qr'))


        else:
            flash("No estás registrado en este evento.", "danger")
            return redirect(url_for('consulta_qr'))
    
