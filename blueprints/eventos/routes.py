from flask import render_template, request, redirect, url_for, flash, send_from_directory, current_app
from . import eventos_bp
from models import db, Evento, Categoria, AdministradorEvento
from utilities.files import save_file
from datetime import datetime


@eventos_bp.route('/crear_evento', methods=['GET','POST'])
def crear_evento():
    if request.method == "POST" and "crear_evento" in request.form:
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        ciudad = request.form.get("ciudad")
        lugar = request.form.get("lugar")
        fecha_inicio_str = request.form.get("fecha_inicio")
        fecha_fin_str = request.form.get("fecha_fin")
        cobro_str = request.form.get("cobro")
        cupos_str = request.form.get("cupos")

        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d") if fecha_inicio_str else None
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d") if fecha_fin_str else None

        cobro = "Sí" if cobro_str == "si" else "No"
        cupos = int(cupos_str) if cupos_str else None

        imagen = request.files.get("imagen")
        imagen_nombre = save_file(
            imagen,
            current_app.config['UPLOAD_FOLDER_IMAGENES'],
            current_app.config['ALLOWED_EXTENSIONS_IMAGENES']
        )

        archivo_programacion = request.files.get("archivo_programacion")
        archivo_nombre = save_file(
            archivo_programacion,
            current_app.config['UPLOAD_FOLDER_PROGRAMACION'],
            current_app.config['ALLOWED_EXTENSIONS_PROGRAMACION']
        )

        admin_demo = AdministradorEvento.query.first()
        if not admin_demo:
            admin_demo = AdministradorEvento(
                adm_id="admin1",
                adm_nombre="Admin Demo",
                adm_correo="demo@admin.com",
                adm_telefono="123456"
            )
            db.session.add(admin_demo)
            db.session.commit()

        nuevo_evento = Evento(
            eve_nombre=nombre,
            eve_descripcion=descripcion,
            eve_ciudad=ciudad,
            eve_lugar=lugar,
            eve_fecha_inicio=fecha_inicio,
            eve_fecha_fin=fecha_fin,
            eve_estado="CREADO",
            adm_id=admin_demo.adm_id,
            cobro=cobro,
            cupos=cupos,
            imagen=imagen_nombre,
            archivo_programacion=archivo_nombre
        )
        db.session.add(nuevo_evento)
        db.session.commit()

        flash(f"¡Se ha creado un nuevo evento! {nombre}")
        return redirect(url_for("super_adm"))

    categorias = Categoria.query.all()
    eventos = Evento.query.all()
    return render_template("eventos/crear_evento.html", eventos=eventos, categorias=categorias)


@eventos_bp.route('/editar_evento/<int:eve_id>', methods=['GET','POST'])
def editar_evento(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    if request.method == "POST":
        evento.eve_nombre = request.form.get("nombre")
        evento.eve_descripcion = request.form.get("descripcion")
        evento.eve_ciudad = request.form.get("ciudad")
        evento.eve_lugar = request.form.get("lugar")
        fecha_inicio_str = request.form.get("fecha_inicio")
        fecha_fin_str = request.form.get("fecha_fin")
        evento.eve_fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d") if fecha_inicio_str else None
        evento.eve_fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d") if fecha_fin_str else None
        evento.cobro = request.form.get("cobro")

        imagen_file = request.files.get("imagen")
        if imagen_file and imagen_file.filename != "":
            imagen_filename = save_file(
                imagen_file,
                current_app.config['UPLOAD_FOLDER_IMAGENES'],
                current_app.config['ALLOWED_EXTENSIONS_IMAGENES']
            )
            if imagen_filename:
                evento.imagen = imagen_filename

        archivo_programacion_file = request.files.get("archivo_programacion")
        if archivo_programacion_file and archivo_programacion_file.filename != "":
            archivo_programacion_filename = save_file(
                archivo_programacion_file,
                current_app.config['UPLOAD_FOLDER_PROGRAMACION'],
                current_app.config['ALLOWED_EXTENSIONS_PROGRAMACION']
            )
            if archivo_programacion_filename:
                evento.archivo_programacion = archivo_programacion_filename

        db.session.commit()
        flash("Evento editado con éxito.")
        return redirect(url_for("lista_eventos"))

    return render_template("eventos/editar_evento.html", evento=evento)


@eventos_bp.route('/cancelar_evento/<int:eve_id>', methods=['POST'])
def cancelar_evento(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    evento.eve_estado = "CANCELADO"
    db.session.commit()
    flash(f"Evento {evento.eve_nombre} cancelado exitosamente.", "success")
    return redirect(url_for("admin.ventana"))


@eventos_bp.route('/activar_evento/<int:eve_id>', methods=['POST'])
def activar_evento(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    evento.eve_estado = "ACTIVO"
    db.session.commit()
    flash(f"Evento {evento.eve_nombre} activado exitosamente.", "success")
    return redirect(url_for("superadmin.eventos_superadmin"))


@eventos_bp.route('/desactivar_evento/<int:eve_id>', methods=['POST'])
def desactivar_evento(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    evento.eve_estado = "INACTIVO"
    db.session.commit()
    flash(f"Evento {evento.eve_nombre} desactivado exitosamente.", "success")
    return redirect(url_for("eventos_superadmin"))


@eventos_bp.route('/descargar_programacion/<int:event_id>')
def descargar_programacion(event_id):
    evento = Evento.query.get_or_404(event_id)
    if not evento.archivo_programacion:
        flash("No hay archivo de programación disponible para este evento.", "danger")
        return redirect(url_for("super_adm"))

    return send_from_directory(
        current_app.config['UPLOAD_FOLDER_PROGRAMACION'],
        evento.archivo_programacion,
        as_attachment=True
    )
