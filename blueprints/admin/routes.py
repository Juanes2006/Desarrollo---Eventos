from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
from markupsafe import Markup
from models import db,Criterio,Instrumento, Participantes, ParticipantesEventos, Asistentes, AsistentesEventos, Area, Categoria, Evento, Calificacion




@admin_bp.route('/administrador_evento')
def ventana():
    eventos = Evento.query.all()   # Obtener todos los eventos
    return render_template('administrador/administrador_evento.html', eventos=eventos)

@admin_bp.route('/gestionar_inscripciones/participante/<int:eve_id>')
def gestionar_inscripciones(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    participantes = db.session.query(
        Participantes.par_id,
        Participantes.par_nombre,
        Participantes.par_correo,
        ParticipantesEventos.par_estado,
        ParticipantesEventos.par_eve_documentos 
    ).join(ParticipantesEventos, Participantes.par_id == ParticipantesEventos.par_eve_participante_fk)\
    .filter(ParticipantesEventos.par_eve_evento_fk == eve_id).all()

    return render_template("administrador/gestionar_inscripciones.html", evento=evento, participantes=participantes)

@admin_bp.route('/gestionar_inscripciones/asistentes/<int:eve_id>')
def gestionar_inscripcion_asis(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    asistentes = db.session.query(
        Asistentes.asi_id,
        Asistentes.asi_nombre,
        Asistentes.asi_correo,
        Asistentes.asi_telefono,
        AsistentesEventos.asi_eve_estado,
        AsistentesEventos.asi_eve_soporte
    ).join(AsistentesEventos, Asistentes.asi_id == AsistentesEventos.asi_eve_asistente_fk)\
    .filter(AsistentesEventos.asi_eve_evento_fk == eve_id).all()
    
    return render_template("administrador/gestionar_inscripciones_asis.html", evento=evento, asistentes=asistentes)

@admin_bp.route('/actualizar_estado', methods=['POST'])
def actualizar_estado():
    par_id = request.form.get('par_id')
    asi_id = request.form.get('asi_id')
    evento_id = request.form.get('evento_id')
    nuevo_estado = request.form.get('estado')

    # Validar que se haya enviado evento_id y al menos uno de los IDs
    if not evento_id or not (par_id or asi_id):
        flash("Error: Faltan datos para actualizar el estado.", "danger")
        return redirect(request.referrer)

    # ✅ CASO PARTICIPANTE
    if par_id:
        participante_evento = ParticipantesEventos.query.filter_by(
            par_eve_participante_fk=par_id,
            par_eve_evento_fk=evento_id
        ).first()

        if participante_evento:
            participante_evento.par_estado = nuevo_estado
            db.session.commit()

            clave_evento = participante_evento.par_eve_clave if participante_evento.par_eve_clave else "No asignada"
            participante = Participantes.query.get(par_id)
            nombre_participante = participante.par_nombre if participante else "Participante"

            if nuevo_estado == "ACEPTADO":
                mensaje = Markup(f"""
                    El participante {nombre_participante} ha sido aceptado, su clave de acceso es: 
                    <strong id='claveEvento'>{clave_evento}</strong>
                    <button class="btn btn-sm btn-outline-primary ml-2" onclick="copiarClave()">📋 Copiar Clave</button>
                """)
                flash(mensaje, "success")
            elif nuevo_estado == "RECHAZADO":
                flash(f"El participante {nombre_participante} ha sido rechazado.", "danger")
            elif nuevo_estado == "PENDIENTE":
                flash(f"El participante {nombre_participante} ha sido puesto en estado pendiente.", "warning")
            else:
                flash(f"El estado de {nombre_participante} ha sido actualizado a {nuevo_estado}.", "success")

            return redirect(url_for("main.lista_eventos", eve_id=evento_id))

    # ✅ CASO ASISTENTE
    if asi_id:
        asistente_evento = AsistentesEventos.query.filter_by(
            asi_eve_asistente_fk=asi_id,
            asi_eve_evento_fk=evento_id
        ).first()

        if asistente_evento:
            asistente_evento.asi_eve_estado = nuevo_estado
            db.session.commit()

            asistente = Asistentes.query.get(asi_id)
            nombre_asistente = asistente.asi_nombre if asistente else "Asistente"

            flash(f"El estado del asistente {nombre_asistente} ha sido actualizado a {nuevo_estado}.", "info")
            return redirect(url_for("main.lista_eventos", eve_id=evento_id))

    # Si no se encontró ni participante ni asistente
    flash("No se encontró la inscripción para actualizar.", "danger")
    return redirect(request.referrer)


@admin_bp.route('/agregar_area', methods=['GET','POST'])
def agregar_area():
    if request.method == "POST":
        are_nombre = request.form.get("are_nombre")
        are_descripcion = request.form.get("are_descripcion")

        # Crear el objeto Area
        nueva_area = Area(are_nombre=are_nombre, are_descripcion=are_descripcion)
        db.session.add(nueva_area)
        db.session.commit()

        flash(f"Área '{are_nombre}' agregada exitosamente.", "success")
        return redirect(url_for("agregar_area"))

    return render_template("superadmin/agregar_area.html")

@admin_bp.route('/agregar_categoria', methods=['GET','POST'])
def agregar_categoria():
    if request.method == "POST":
        cat_nombre = request.form.get("cat_nombre")
        cat_descripcion = request.form.get("cat_descripcion")
        cat_area_fk = request.form.get("cat_area_fk")  # Este valor es el ID del área seleccionada

        # Crear el objeto Categoria
        nueva_categoria = Categoria(
            cat_nombre=cat_nombre,
            cat_descripcion=cat_descripcion,
            cat_area_fk=cat_area_fk
        )
        db.session.add(nueva_categoria)
        db.session.commit()

        flash(f"Categoría '{cat_nombre}' agregada exitosamente al área.", "success")
        return redirect(url_for("agregar_categoria"))

    # Para el método GET, obtener todas las áreas disponibles para el select
    areas = Area.query.all()
    return render_template("agregar_categoria.html", areas=areas)


@admin_bp.route('/estadisticas')

def ver_estadisticas():
    
    eventos = Evento.query.all()

    estadisticas = []

    for evento in eventos:
        total_asistentes = AsistentesEventos.query.filter_by(asi_eve_evento_fk=evento.eve_id).count()
        total_participantes = ParticipantesEventos.query.filter_by(par_eve_evento_fk=evento.eve_id).count()

        estadisticas.append({
            'evento_id': evento.eve_id,
            'evento_nombre': evento.eve_nombre,
            'asistentes': total_asistentes,
            'participantes': total_participantes,
            'total': total_asistentes + total_participantes,
            'porcentaje_participantes': (total_participantes / (total_asistentes + total_participantes) * 100) if (total_asistentes + total_participantes) > 0 else 0
        })

    return render_template('administrador/estadisticas.html', estadisticas=estadisticas)

@admin_bp.route("/admin/evento/<int:evento_id>/toggle_inscripcion/<string:tipo>", methods=["POST"])
def toggle_inscripcion(evento_id, tipo):
    evento = Evento.query.get_or_404(evento_id)

    if tipo == "participantes":
        evento.inscripciones_participantes_abiertas = not evento.inscripciones_participantes_abiertas
    elif tipo == "asistentes":
        evento.inscripciones_asistentes_abiertas = not evento.inscripciones_asistentes_abiertas
    else:
        flash("Tipo de inscripción no válido.", "danger")
        return redirect(request.referrer)

    db.session.commit()
    flash("Estado de inscripciones actualizado correctamente.", "success")
    return redirect(request.referrer)

# Listar y agregar criterios
@admin_bp.route('/criterios', methods=['GET', 'POST'])
def gestionar_criterios():
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
            flash('Faltan datos', 'danger')

        return redirect(url_for('administrador.gestionar_criterios'))
    
    criterios = Criterio.query.all()
    return render_template('administrador/criterios.html', criterios=criterios)

# Editar criterio
@admin_bp.route('/criterios/<int:criterio_id>/editar', methods=['GET', 'POST'])
def editar_criterio(criterio_id):
    criterio = Criterio.query.get_or_404(criterio_id)
    if request.method == 'POST':
        criterio.cri_descripcion = request.form.get('descripcion')
        criterio.cri_peso = request.form.get('peso')
        criterio.cri_evento_fk = request.form.get('evento_id')
        db.session.commit()
        flash('Criterio actualizado', 'success')
        return redirect(url_for('administrador.gestionar_criterios'))
    return render_template('administrador/editar_criterio.html', criterio=criterio)

# Eliminar criterio
@admin_bp.route('/criterios/<int:criterio_id>/eliminar', methods=['POST'])
def eliminar_criterio(criterio_id):
    criterio = Criterio.query.get_or_404(criterio_id)
    db.session.delete(criterio)
    db.session.commit()
    flash('Criterio eliminado', 'success')
    return redirect(url_for('administrador.gestionar_criterios'))


@admin_bp.route('/instrumentos', methods=['GET', 'POST'])
def cargar_instrumentos():
    if request.method == 'POST':
        tipo_instrumento = request.form.get('tipo_instrumento')
        descripcion_instrumento = request.form.get('descripcion_instrumento')
        evento_id = request.form.get('evento_id')
        
        # Validación básica para verificar que los campos no estén vacíos
        if tipo_instrumento and descripcion_instrumento and evento_id:
            nuevo_instrumento = Instrumento(
                inst_tipo=tipo_instrumento,
                inst_descripcion=descripcion_instrumento,
                inst_evento_fk=int(evento_id)
            )
            db.session.add(nuevo_instrumento)
            db.session.commit()
            flash('Instrumento cargado correctamente', 'success')
        else:
            flash('Debes completar todos los campos', 'danger')
        
        return redirect(url_for('admin.cargar_instrumentos'))
    
    # Consulta todos los instrumentos para mostrarlos
    instrumentos = Instrumento.query.all()
    return render_template('administrador/instrumentos.html', instrumentos=instrumentos)



# Para administrador y evaluador
@admin_bp.route('/calificaciones/<int:participante_id>')
def ver_calificaciones(participante_id):
    calificaciones = Calificacion.query.filter_by(cal_participante_fk=participante_id).all()
    participante = Participantes.query.get_or_404(participante_id)
    return render_template('administrador/ver_calificaciones.html', calificaciones=calificaciones, participante=participante)



@admin_bp.route('/ranking/<int:evento_id>')
def ver_ranking(evento_id):
    # Obtener todos los participantes de ese evento
    participantes = Participantes.query.filter_by(par_evento_fk=evento_id).all()
    
    ranking = []

    for participante in participantes:
        # Sumar todos los puntajes del participante
        puntajes = Calificacion.query.filter_by(cal_participante_fk=participante.id).all()
        total_puntaje = sum([p.puntaje for p in puntajes])
        
        ranking.append({
            'participante': participante,
            'total_puntaje': total_puntaje
        })

    # Ordenar de mayor a menor puntaje
    ranking.sort(key=lambda x: x['total_puntaje'], reverse=True)

    return render_template('participantes/ranking.html', ranking=ranking)
