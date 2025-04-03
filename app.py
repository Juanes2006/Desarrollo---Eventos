
from flask   import Flask, render_template, redirect, url_for, flash,request, send_file, make_response, current_app, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from flask_migrate import Migrate
from datetime import datetime, date
from sqlalchemy.orm import joinedload
from io import BytesIO
import segno
import base64
import os
from sqlalchemy.dialects.mysql import ENUM

from werkzeug.utils import secure_filename



app = Flask(__name__)
app.secret_key = "clave_secreta_para_flash"



UPLOAD_FOLDER_IMAGENES = os.path.join(app.root_path, 'static', 'imagenes')
UPLOAD_FOLDER_PAGOS = os.path.join(app.root_path, 'static', 'uploads')  
UPLOAD_FOLDER_PROGRAMACION = os.path.join(app.root_path, 'static', 'programacion')
UPLOAD_FOLDER = UPLOAD_FOLDER_PAGOS  # Default upload folder

# Extensiones permitidas
ALLOWED_EXTENSIONS_IMAGENES = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS_PAGOS = {'png', 'jpg', 'pdf'}
ALLOWED_EXTENSIONS_PROGRAMACION = {'pdf'}

# Configurar diferentes rutas en app.config
app.config['UPLOAD_FOLDER_IMAGENES'] = UPLOAD_FOLDER_IMAGENES
app.config['UPLOAD_FOLDER_PROGRAMACION'] = UPLOAD_FOLDER_PROGRAMACION
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Add default upload folder to config
app.config['UPLOAD_FOLDER_PROGRAMACION'] = UPLOAD_FOLDER_PROGRAMACION

# Función para verificar extensión permitida
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Función para guardar archivos en la carpeta correcta
def save_file(file, folder, allowed_extensions):
    if file and allowed_file(file.filename, allowed_extensions):
        filename = secure_filename(file.filename)
        os.makedirs(folder, exist_ok=True)  # Crea la carpeta si no existe
        file.save(os.path.join(folder, filename))
        return filename
    return None


# ------------------------------------------------------------------
# CONFIGURACIÓN DE LA BASE DE DATOS
# ------------------------------------------------------------------
# Conexión a MySQL con pymysql
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/eventos_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)



# Tabla: ADMINISTRADORES_EVENTO
class AdministradorEvento(db.Model):
    __tablename__ = 'administradores_evento'
    adm_id = db.Column(db.String(20), primary_key=True)
    adm_nombre = db.Column(db.String(100))
    adm_correo = db.Column(db.String(100))
    adm_telefono = db.Column(db.String(45))
    # Relación uno (admin) a muchos (eventos)
    eventos = db.relationship("Evento", backref="administrador")

# Tabla: AREAS
class Area(db.Model):
    __tablename__ = 'areas'
    are_codigo = db.Column(db.Integer, primary_key=True)
    are_nombre = db.Column(db.String(45))
    are_descripcion = db.Column(db.String(400))
    # Relación uno (area) a muchos (categorias)
    categorias = db.relationship("Categoria", backref="area")

# Tabla: CATEGORIAS
class Categoria(db.Model):
    __tablename__ = 'categorias'
    cat_codigo = db.Column(db.Integer, primary_key=True)
    cat_nombre = db.Column(db.String(45))
    cat_descripcion = db.Column(db.String(400))
    cat_area_fk = db.Column(db.Integer, db.ForeignKey('areas.are_codigo'))

# Tabla intermedia para la relación muchos-a-muchos EVENTOS_CATEGORIAS
class EventoCategoria(db.Model):
    __tablename__ = 'eventos_categorias'
    eve_cat_evento_fk = db.Column(db.Integer, db.ForeignKey('eventos.eve_id'), primary_key=True)
    eve_cat_categoria_fk = db.Column(db.Integer, db.ForeignKey('categorias.cat_codigo'), primary_key=True)


# Tabla: EVENTOS
class Evento(db.Model):
    __tablename__ = 'eventos'
    eve_id = db.Column(db.Integer, primary_key=True)
    eve_nombre = db.Column(db.String(100), nullable=False)
    eve_descripcion = db.Column(db.String(400))
    eve_ciudad = db.Column(db.String(45))
    eve_lugar = db.Column(db.String(45))
    eve_fecha_inicio = db.Column(db.Date)
    eve_fecha_fin = db.Column(db.Date)
    eve_estado = db.Column(db.String(45))
    adm_id = db.Column(db.String(20), db.ForeignKey('administradores_evento.adm_id'))
    
    # Change from Float to String with "Sí" or "No"
    cobro = db.Column(db.String(2), nullable=False, default="No")

    cupos = db.Column(db.Integer, nullable=True)
    
    imagen = db.Column(db.String(255), nullable=True)
     
    ## AGREGO UN NUEVO CAMPO PARA EL ARCHIVO DE PROGRAMACION
    # Este campo almacenará la ruta del archivo de programación
    archivo_programacion = db.Column(db.String(255), nullable=True)  # Nuevo campo para el archivo



    
    # Relaciones muchos-a-muchos
    categorias = db.relationship('Categoria', secondary='eventos_categorias', backref='eventos')


# -----------------------------------------------------------
#  NUEVAS TABLAS (DIAGRAMA DE ASISTENTES / PARTICIPANTES)
# -----------------------------------------------------------

# Tabla: ASISTENTES
class Asistentes(db.Model):
    __tablename__ = 'asistentes'
    asi_id = db.Column(db.String(20), primary_key=True)
    asi_nombre = db.Column(db.String(100))
    asi_correo = db.Column(db.String(100))
    asi_telefono = db.Column(db.String(20))

    asistentes_eventos = db.relationship('AsistentesEventos', backref='asistente', lazy=True)


# Tabla: ASISTENTES_EVENTOS
class AsistentesEventos(db.Model):
    __tablename__ = 'asistentes_eventos'
    asi_eve_asistente_fk = db.Column(db.String(20), db.ForeignKey('asistentes.asi_id'), primary_key=True)
    asi_eve_evento_fk = db.Column(db.Integer, db.ForeignKey('eventos.eve_id'), primary_key=True)

    asi_eve_fecha_hora = db.Column(db.DateTime)
    asi_eve_soporte = db.Column(db.String(255), nullable=True)
    asi_eve_estado = db.Column(db.String(45))
    asi_eve_clave = db.Column(db.String(45))

  


# Tabla: PARTICIPANTES


class Participantes(db.Model):
    __tablename__ = 'participantes'
    par_id = db.Column(db.String(20), primary_key=True)
    par_nombre = db.Column(db.String(100))
    par_correo = db.Column(db.String(100))
    par_telefono = db.Column(db.String(45))
    
    # Relación uno a muchos con ParticipantesEventos
    participantes_eventos = db.relationship('ParticipantesEventos', backref='participante', lazy=True)



# Tabla: PARTICIPANTES_EVENTOS
class ParticipantesEventos(db.Model):
    __tablename__ = 'participantes_eventos'
    
    par_eve_participante_fk = db.Column(db.String(20), db.ForeignKey('participantes.par_id'), primary_key=True)
    par_eve_evento_fk = db.Column(db.Integer, db.ForeignKey('eventos.eve_id'), primary_key=True)

    par_eve_fecha_hora = db.Column(db.DateTime)
    par_eve_documentos = db.Column(db.String(255), nullable=True)
    par_eve_or = db.Column(db.String(255), nullable=True)
    par_eve_clave = db.Column(db.String(45))
    par_estado = db.Column(ENUM('PENDIENTE', 'ACEPTADO', 'RECHAZADO'), nullable=False, default='PENDIENTE')
   

   
# CREAR LAS TABLAS



with app.app_context():
    db.create_all()

# HISTORIAS DE USUARIO







# HU01: Ver los diferentes eventos próximos a realizarse
@app.route('/visitante_web')
def visitante():
    return render_template('visitante_web.html')

@app.route('/administrador_evento')
def ventana():
    eventos = Evento.query.all()   # Obtener todos los eventos
    return render_template('administrador_evento.html', eventos=eventos)


@app.route('/super_admin')
def super_adm():
    eventos = Evento.query.all()  # Obtener todos los eventos
    return render_template('super_admin.html', eventos=eventos)

@app.route("/superadmin/eventos", methods=["GET", "POST"])
def eventos_superadmin():
    if request.method == "POST":
        pass
    eventos = Evento.query.all()
    return render_template("super_admin.html", eventos=eventos)



@app.route("/eventos_proximos")
def eventos_proximos():
    hoy = date.today()
    eventos = Evento.query.filter_by(eve_estado="ACTIVO").all()

    return render_template("lista_eventos.html", titulo="Eventos Próximos", eventos=eventos)

# HU02: Realizar búsquedas de eventos de mi interés usando diferentes filtros
@app.route("/visitante_web/buscar_eventos", methods=["GET", "POST"])
def buscar_eventos():
    eventos = []
    if request.method == "POST":
        # Recoger los parámetros de búsqueda desde el formulario
        nombre = request.form.get("nombre", "").strip()
        fecha_inicio_str = request.form.get("fecha_inicio", "").strip()
        ciudad = request.form.get("ciudad", "").strip()
        
        # Inicia la consulta base
        query = Evento.query
        
        # Agrega el filtro para el nombre si se ha ingresado
        if nombre:
            query = query.filter(Evento.eve_nombre.contains(nombre))
            
        
        
        # Agrega el filtro para la fecha (ejemplo: eventos que comienzan a partir de una fecha)
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                query = query.filter(Evento.eve_fecha_inicio >= fecha_inicio)
            except ValueError:
                flash("Formato de fecha inválido. Usa AAAA-MM-DD.")
        
        # Agrega el filtro para la ciudad si se ha ingresado
        if ciudad:
            query = query.filter(Evento.eve_ciudad.contains(ciudad))
        
        eventos = query.all()
        flash("Resultados de la búsqueda")
        
    return render_template("buscar_eventos.html", eventos=eventos)


@app.route("/administrador/crear_evento", methods=["GET", "POST"])
def crear_evento():
        if request.method == "POST":
            # Verifica que sea el formulario de creación
            if "crear_evento" in request.form:
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
                
                # Procesa cobro y cupos si se envían, de lo contrario deja None
                cobro = "Sí" if cobro_str == "si" else "No"  # Guarda como "Sí" o "No"

                cupos = int(cupos_str) if cupos_str else None
                
                
                # Guardar la imagen del evento
                imagen = request.files.get("imagen")
                imagen_nombre = save_file(imagen, app.config['UPLOAD_FOLDER_IMAGENES'], ALLOWED_EXTENSIONS_IMAGENES)

        # Guardar comprobante de pago
        

        # Guardar archivo de programación
                archivo_programacion = request.files.get("archivo_programacion")
                archivo_nombre = save_file(archivo_programacion, app.config['UPLOAD_FOLDER_PROGRAMACION'], ALLOWED_EXTENSIONS_PROGRAMACION)

                
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
                    imagen=imagen_nombre,  # Guarda el nombre de la imagen
                    archivo_programacion=archivo_nombre  # Guarda el nombre del archivo de programación
                )
                db.session.add(nuevo_evento)
                db.session.commit()
    
                flash(f"¡Se ha creado un nuevo evento! {nombre}")
    
                return redirect(url_for("super_adm"))
        categorias = Categoria.query.all()
        eventos = Evento.query.all()  # Obtiene todos los eventos creados
        return render_template("crear_evento.html", eventos=eventos, categorias=categorias)

# HU03: Acceder a información detallada sobre los eventos de mi interés
@app.route("/evento_detalle/<int:eve_id>")
def evento_detalle(eve_id):
    evento = (
        Evento.query
        .filter_by(eve_id=eve_id)
        .options(
            joinedload(Evento.categorias).joinedload(Categoria.area)  # Carga las categorías y áreas
        )
        .first_or_404()
    )

    return render_template("detalle_evento.html", evento=evento)





@app.route('/eventos/<int:evento_id>/registrarme', methods=['GET', 'POST'])
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
            if evento.cobro == 'SI' and 'soporte_pago' in request.files:
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
        flash(f"¡Te has registrado exitosamente como {tipo}!", "success")
        return redirect(url_for('lista_eventos'))
    
    # Si la solicitud es GET, simplemente renderizamos el formulario
    return render_template('formulario_registro.html', evento=evento)

# Ruta para mostrar el formulario de consulta de QR
# Ejemplo de ruta que obtiene los eventos de la BD
@app.route('/consulta_qr', methods=['GET', 'POST'])
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

        return redirect(url_for('mostrar_qr', event_id=event_id, user_id=user_id))

    return render_template('consulta_qr.html', events=events)


# Ruta para mostrar el QR y los detalles del evento seleccionado
@app.route('/mostrar_qr/<int:event_id>/<string:user_id>')
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
        return redirect(url_for('consulta_qr'))
    
    # ✅ Verificar si el participante fue aceptado
    if participante_evento and participante_evento.par_estado != "ACEPTADO":
        flash("Tu inscripción aún no ha sido aceptada. No puedes obtener el QR.", "danger")
        return redirect(url_for('consulta_qr'))

    # ✅ Verificar si el asistente fue aceptado (si aplica)
    if asistente_evento and asistente_evento.asi_eve_estado != "ACEPTADO":
        flash("Tu asistencia aún no ha sido confirmada. No puedes obtener el QR.", "danger")
        return redirect(url_for('consulta_qr'))

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
        return redirect(url_for('consulta_qr'))
    
    return render_template(
        'mostrar_qr.html',
        qr_image=qr_b64,
        evento=evento,  
        registration_type=registration_type,
        user_document=user_document,
        user_id=user_id
    )

    

# Ruta para descargar el QR (opcional)
@app.route('/descargar_qr/<int:event_id>/<string:user_id>')
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




#HU10: CANCELAR INSCRIPCIÓN A UN EVENTO
@app.route('/cancelar_inscripcion/<int:evento_id>/<string:user_id>', methods=['GET','POST'])
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
    
@app.route("/descargar_programacion/<int:event_id>")
def descargar_programacion(event_id):
    # Buscar el evento en la base de datos
    evento = Evento.query.get_or_404(event_id)

    # Verificar si el evento tiene un archivo de programación
    if not evento.archivo_programacion:
        flash("No hay archivo de programación disponible para este evento.", "danger")
        return redirect(url_for("super_adm"))  # Redirige a la página de administración

    # Ruta completa del archivo
    return send_from_directory(app.config['UPLOAD_FOLDER_PROGRAMACION'], evento.archivo_programacion, as_attachment=True)
############ FUNCION PARA VER SI ES UN PARTICIPANTE
@app.route('/verificar_participante', methods=['GET', 'POST'])
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


#########  HU15: Modificar la información de un participante
@app.route('/modificar_participante/<string:user_id>', methods=['GET', 'POST'])
def modificar_participante(user_id):
    participante = Participantes.query.get(user_id)
    
    if not participante:
        flash("Participante no encontrado", "danger")
        return redirect(url_for('consulta_qr'))  # Redirige a la consulta QR si no se encuentra el participante

    if request.method == 'POST':
        participante.par_nombre = request.form['nombre']
        participante.par_correo = request.form['correo']
        participante.par_telefono = request.form['telefono']

        # Si se sube un nuevo documento, lo guardamos
        if 'documento' in request.files:
            file = request.files['documento']
            if file.filename != '':
                filename = save_file(file, app.config['UPLOAD_FOLDER_PAGOS'], ALLOWED_EXTENSIONS_PAGOS)
                if filename:
                    participante.par_eve_documentos = filename

        db.session.commit()
        flash("Información actualizada con éxito", "success")
        return redirect(url_for('consulta_qr'))  # Redirige tras modificar

    return render_template('modificar_participante.html', participante=participante)


@app.route('/admin/gestionar_inscripciones/<int:eve_id>')
def gestionar_inscripciones(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    participantes = db.session.query(
        Participantes.par_id,
        Participantes.par_nombre,
        Participantes.par_correo,
        ParticipantesEventos.par_estado
    ).join(ParticipantesEventos, Participantes.par_id == ParticipantesEventos.par_eve_participante_fk)\
    .filter(ParticipantesEventos.par_eve_evento_fk == eve_id).all()

    return render_template("gestionar_inscripciones.html", evento=evento, participantes=participantes)


####### FUNCION ADICIONAL PARA ACTUALIZAR EL ESTADO DE LOS PARTICIPANTES
@app.route('/admin/actualizar_estado', methods=['POST'])
def actualizar_estado():
    par_id = request.form.get('par_id')
    evento_id = request.form.get('evento_id')
    nuevo_estado = request.form.get('estado')

    # Validar que se enviaron los datos necesarios
    if not par_id or not evento_id:
        flash("Error: Faltan datos para actualizar el estado.", "danger")
        return redirect(request.referrer)

    # Buscar al participante en la tabla ParticipantesEventos para ese evento específico
    participante_evento = ParticipantesEventos.query.filter_by(
        par_eve_participante_fk=par_id,
        par_eve_evento_fk=evento_id
    ).first()

    if participante_evento:
        participante_evento.par_estado = nuevo_estado  # ✅ Asegúrate de que la columna correcta es 'par_estado'
        db.session.commit()

        # Obtener la clave del evento si existe
        clave_evento = participante_evento.par_eve_clave if participante_evento.par_eve_clave else "No asignada"

        # Obtener el nombre del participante
        participante = Participantes.query.get(par_id)
        nombre_participante = participante.par_nombre if participante else "Participante"

        # Mensajes de notificación según el estado
        if nuevo_estado == "ACEPTADO":
            mensaje = Markup(f"""
                El participante {nombre_participante} ha sido aceptado, su clave de acceso es: 
                <strong id='claveEvento'>{clave_evento}</strong>
                <button class="btn btn-sm btn-outline-primary ml-2" onclick="copiarClave()">📋 Copiar Clave</button>
            """)
            flash(mensaje, "success")
            return redirect(url_for("lista_eventos", eve_id=evento_id))  # Redirige a la gestión del evento
   
        elif nuevo_estado == "RECHAZADO":
            flash(f"El participante {nombre_participante} ha sido rechazado.", "danger")
            return redirect(url_for("lista_eventos", eve_id=evento_id))  # Redirige a la gestión del evento

        elif nuevo_estado == "PENDIENTE":
            flash(f"El participante {nombre_participante} ha sido puesto en estado pendiente.", "warning")
            return redirect(url_for("lista_eventos", eve_id=evento_id))  # Redirige a la gestión del evento

        else:
            flash(f"El estado de {nombre_participante} ha sido actualizado a {nuevo_estado}.", "success")
            return redirect(url_for("lista_eventos", eve_id=evento_id))  # Redirige a la gestión del evento


        return redirect(url_for("gestionar_inscripciones", eve_id=evento_id))  # Redirige a la gestión del evento

    flash("No se encontró la inscripción de este participante en el evento.", "danger")
    return redirect(request.referrer)



# HU52: Editar la información de un evento 
@app.route("/administrador/editar_evento/<int:eve_id>", methods=["GET", "POST"])
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
        
        imagen_file= request.files.get("imagen")
        if imagen_file and imagen_file.filename != "":
            imagen_filename = save_file(imagen_file)
            if imagen_filename:
                evento.imagen = imagen_filename
                
        archivo_programacion_file = request.files.get("archivo_programacion")
        if archivo_programacion_file and archivo_programacion_file.filename != "":
            archivo_programacion_filename = save_file(archivo_programacion_file, app.config['UPLOAD_FOLDER_PROGRAMACION'], ALLOWED_EXTENSIONS_PROGRAMACION)
            if archivo_programacion_filename:
                evento.archivo_programacion = archivo_programacion_filename

        db.session.commit()
        flash("Evento editado con éxito.")
        return redirect(url_for("lista_eventos"))
    return render_template("editar_evento.html", evento=evento)





# HU90: Ver listado de los eventos activos
@app.route("/eventos_activos")
def eventos_activos():
    eventos = Evento.query.filter(Evento.eve_estado.in_(["CREADO", "ACTIVO"])).all()
    return render_template("lista_eventos.html", titulo="Eventos Activos", eventos=eventos)

# HU91: Acceder a la información de un evento en particular
@app.route("/superadmin/evento/<int:eve_id>")
def ver_evento_superadmin(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    return render_template("detalle_evento_superadmin.html", evento=evento)

@app.route("/activar_evento/<int:eve_id>", methods=["POST"])
def activar_evento(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    evento.eve_estado = "ACTIVO"
    db.session.commit()
    flash(f"Evento {evento.eve_nombre} activado exitosamente.", "success")
    return redirect(url_for("eventos_superadmin"))


@app.route("/desactivar_evento/<int:eve_id>", methods=["POST"])
def desactivar_evento(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    evento.eve_estado = "INACTIVO"
    db.session.commit()
    flash(f"Evento {evento.eve_nombre} desactivado exitosamente.", "success")
    return redirect(url_for("eventos_superadmin"))  



@app.route("/superadmin/agregar_area", methods=["GET", "POST"])
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

    return render_template("agregar_area.html")

@app.route("/superadmin/agregar_categoria", methods=["GET", "POST"])
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




# RUTA GENÉRICA PARA LISTAR TODOS LOS EVENTOS
@app.route("/")
@app.route("/visitante_web/lista_eventos")
def lista_eventos():
    eventos = Evento.query.filter_by(eve_estado="Activo").all()
    return render_template("lista_eventos.html", titulo="Eventos Activos", eventos=eventos)


@app.route("/participante/mi_info", methods=["GET", "POST"])
def mi_info():
    participante = None
    eventos_inscritos = []

    if request.method == "POST":
        par_id = request.form.get("par_id")

        if par_id:
            # Obtener la información básica del participante
            participante = Participantes.query.filter_by(par_id=par_id).first()
            
            if participante:
                # Obtener los eventos en los que está inscrito y que estén activos
                eventos_inscritos = db.session.query(
                    Evento.eve_nombre,
                    Evento.eve_fecha_inicio,
                    Evento.eve_ciudad,
                    ParticipantesEventos.par_estado,
                    ParticipantesEventos.par_eve_documentos
                ).join(ParticipantesEventos, Evento.eve_id == ParticipantesEventos.par_eve_evento_fk)\
                 .filter(ParticipantesEventos.par_eve_participante_fk == par_id, Evento.eve_estado == "ACTIVO")\
                 .all()
            else:
                flash("No se encontró información para el ID proporcionado.", "danger")

    return render_template("par_informacion.html", 
                           titulo="Mis Eventos Inscritos", 
                           participante=participante, 
                           eventos_inscritos=eventos_inscritos)

# PUNTO DE ENTRADA
if __name__ == "__main__":
    app.run(debug=True)
