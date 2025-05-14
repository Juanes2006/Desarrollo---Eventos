from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
import io
import csv
from flask import make_response
from sqlalchemy import func, desc
from markupsafe import Markup
from models import db,Criterio,Instrumento,evaluador_evento, Participantes, ParticipantesEventos, Asistentes, AsistentesEventos, Area, Categoria, Evento, Calificacion, AdministradorEvento, Evaluador




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
     .filter(ParticipantesEventos.par_eve_evento_fk == eve_id)\
     .all()
     
    

    return render_template("administrador/gestionar_inscripciones.html", 
                           evento=evento, 
                           participantes=participantes)

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
        return redirect(url_for("admin.agregar_area"))

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
        return redirect(url_for("admin.agregar_categoria"))

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


# Editar criterio
#@admin_bp.route('/criterios/<int:criterio_id>/editar', methods=['GET', 'POST'])
#def editar_criterio(criterio_id):
    #criterio = Criterio.query.get_or_404(criterio_id)
    #if request.method == 'POST':
        #criterio.cri_descripcion = request.form.get('descripcion')
        #criterio.cri_peso = request.form.get('peso')
        #criterio.cri_evento_fk = request.form.get('evento_id')
       # db.session.commit()
      #  flash('Criterio actualizado', 'success')
     #   return redirect(url_for('admin.gestionar_criterios'))
    #return render_template('administrador/editar_criterio.html', criterio=criterio)

# Eliminar criterio
#@admin_bp.route('/criterios/<int:criterio_id>/eliminar', methods=['POST'])
#def eliminar_criterio(criterio_id):
 #   criterio = Criterio.query.get_or_404(criterio_id)
  #  db.session.delete(criterio)
   # db.session.commit()
    #flash('Criterio eliminado', 'success')
    #return redirect(url_for('administrador.gestionar_criterios'))


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
        
        return redirect(url_for('admin.'))
    
    # Consulta todos los instrumentos para mostrarlos
    instrumentos = Instrumento.query.all()
    return render_template('administrador/cargar_instrumento.html', instrumentos=instrumentos)



# Para administrador y evaluador
@admin_bp.route('/criterios/<int:evento_id>', methods=['GET', 'POST'])
def gestionar_criterios_admin(evento_id):
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
        'administrador/criterios.html',
        criterios=criterios,
        instrumento=instrumento,
        evento_id=evento_id,
        total_peso=round(total_peso, 2),
        evento=evento
    )

    # Verificación del total actual para mostrar feedback
    


# Ruta para cargar el instrumento de evaluación
@admin_bp.route('/administrador/evento/<int:evento_id>/instrumento', methods=['GET', 'POST'])
def cargar_instrumento_admin(evento_id):
    evento = Evento.query.get_or_404(evento_id)

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

        return redirect(url_for('admin.ventana', evento_id=evento_id))

    return render_template('administrador/cargar_instrumento.html', instrumento=instrumento_existente, evento_id=evento_id, evento=evento)
from sqlalchemy import func, desc
@admin_bp.route('/administrador/evento/<int:evento_id>/ranking')
def ver_ranking_admin(evento_id):
    """
    Muestra el ranking (tabla de posiciones) de todos los participantes 
    en el evento, calculando la suma ponderada de sus calificaciones.
    Solo debería accederse si el evaluador (eva_id) tiene permiso sobre el evento.
    """

    # 1. Verificar la existencia del evaluador y evento (opcional, según tu control)
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
    return render_template('administrador/ranking.html',
                           
                           evento=evento,
                           ranking=ranking)
    
from collections import defaultdict

@admin_bp.route('/administrador/evento/<int:evento_id>/calificaciones')
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
        'administrador/ver_calificaciones.html',
        evento=evento,
        participantes=participantes_calificados
    )
@admin_bp.route('/administrador/evento/<int:evento_id>/calificaciones/participante/<int:participante_id>')
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
        'administrador/calificaciones_participante.html',
        evento=evento,
        participante=participante,
        calificaciones=calificaciones
    )


    # Agrupar por participante
    calificaciones = defaultdict(list)
    for par_nombre, cri_descripcion, eva_nombre, cal_valor in calificaciones_raw:
        calificaciones[par_nombre].append({
            'criterio': cri_descripcion,
            'evaluador': eva_nombre,
            'valor': cal_valor
        })

    return render_template('administrador/ver_calificaciones.html', evento=evento, calificaciones=calificaciones)


@admin_bp.route('/agregar_evaluador', methods=['GET', 'POST'])
def agregar_evaluador():
    if request.method == 'POST':
        eva_id = request.form.get('eva_id')
        eva_nombre = request.form.get('eva_nombre')
        eva_correo = request.form.get('eva_correo')
        eva_telefono = request.form.get('eva_telefono')
        eventos_ids = request.form.getlist('eventos')  # <-- recibe lista de eventos

        if eva_id and eva_nombre and eva_correo and eva_telefono:
            nuevo_evaluador = Evaluador(
                eva_id=eva_id,
                eva_nombre=eva_nombre,
                eva_correo=eva_correo,
                eva_telefono=eva_telefono
            )
            # Asignar eventos seleccionados
            for evento_id in eventos_ids:
                evento = Evento.query.get(evento_id)
                if evento:
                    nuevo_evaluador.eventos.append(evento)

            db.session.add(nuevo_evaluador)
            db.session.commit()
            flash('Evaluador agregado correctamente', 'success')
            return redirect(url_for('admin.agregar_evaluador'))
        else:
            flash('Faltan datos', 'danger')

    # PARA EL FORMULARIO: trae todos los eventos disponibles
    eventos = Evento.query.all()
    return render_template('administrador/registrar_evaluador.html', eventos=eventos)

@admin_bp.route('/evaluador/<string:eva_id>/editar', methods=['GET', 'POST'])
def editar_evaluador(eva_id):
    evaluador = Evaluador.query.get_or_404(eva_id)
    eventos = Evento.query.all()

    if request.method == 'POST':
        # Actualizar datos personales
        evaluador.eva_nombre = request.form.get('eva_nombre')
        evaluador.eva_correo = request.form.get('eva_correo')
        evaluador.eva_telefono = request.form.get('eva_telefono')

        # Actualizar eventos asignados
        eventos_seleccionados = request.form.getlist('eventos')  # Obtiene lista de eventos seleccionados
        eventos_objetos = Evento.query.filter(Evento.eve_id.in_(eventos_seleccionados)).all()
        evaluador.eventos = eventos_objetos  # Reasigna completamente los eventos

        db.session.commit()
        flash('Evaluador actualizado correctamente.', 'success')
        return redirect(url_for('admin.ventana'))  # O donde quieras redirigir

    return render_template('administrador/editar_evaluador.html', evaluador=evaluador, eventos=eventos)

@admin_bp.route('/evaluador/<string:eva_id>/eliminar', methods=['POST', 'GET'])
def eliminar_evaluador(eva_id):
    evaluador = Evaluador.query.get_or_404(eva_id)

    # Quitar eventos si tienes relación muchos-a-muchos
    evaluador.eventos.clear()

    db.session.delete(evaluador)
    db.session.commit()

    flash('Evaluador eliminado correctamente.', 'success')
    return redirect(url_for('admin.ventana'))  # o donde quieras redirigir después


@admin_bp.route('/gestionar_evaluadores/<int:eve_id>')
def gestionar_evaluadores(eve_id):
    evento = Evento.query.get_or_404(eve_id)

    # Consultar evaluadores asignados al evento
    evaluadores = db.session.query(
        Evaluador.eva_id,
        Evaluador.eva_nombre,
        Evaluador.eva_correo,
        Evaluador.eva_telefono
    ).join(
        evaluador_evento, Evaluador.eva_id == evaluador_evento.c.evaluador_id
    ).filter(
        evaluador_evento.c.evento_id == eve_id
    ).all()

    return render_template("administrador/gestionar_evaluadores.html", 
                           evento=evento, 
                           evaluadores=evaluadores)

from flask import Response

@admin_bp.route('/admin/evento/<int:evento_id>/descargar_ranking')
def descargar_ranking(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    # Buscar los participantes de este evento
    participantes_evento = ParticipantesEventos.query.filter_by(par_eve_evento_fk=evento_id).all()
    data = []
    for pe in participantes_evento:
        participante = pe.participante  # gracias a backref
        # Calificaciones de ese participante
        calificaciones = Calificacion.query.filter_by(cal_participante_fk=participante.par_id).all()
        puntaje_total = sum(c.cal_valor for c in calificaciones)

        data.append({
            'participante_id': participante.par_id,
            'participante_nombre': participante.par_nombre,
            'puntaje_total': puntaje_total
        })

    # Ordenar por puntaje total descendente
    data.sort(key=lambda x: x['puntaje_total'], reverse=True)

    # Crear el CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Encabezados del CSV
    headers = ["Posición", "Participante", "Puntaje Total"]
    writer.writerow(headers)

    # Escribir filas de datos
    for posicion, participante in enumerate(data, start=1):
        participante_nombre = participante.get('participante_nombre', 'Nombre Desconocido')
        participante_id = participante.get('participante_id', 'ID Desconocido')
        puntaje_total = participante.get('puntaje_total', 0)

        fila = [
            posicion,
            f"{participante_nombre} ({participante_id})",
            "{:.2f}".format(puntaje_total)
        ]
        writer.writerow(fila)


    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=ranking_evento_{evento_id}.csv"}
    )
