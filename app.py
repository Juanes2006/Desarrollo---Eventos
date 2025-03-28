
from flask import Flask, render_template, redirect, url_for, flash,request, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, date
from sqlalchemy.orm import joinedload
from io import BytesIO
import segno
import base64
import os
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.secret_key = "clave_secreta_para_flash"



# Configuración para la subida de imágenes
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'imagenes')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    """
    Guarda la imagen en la carpeta UPLOAD_FOLDER y retorna el nombre seguro del archivo.
    Si el archivo no es permitido, retorna None.
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
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
    # Obtener todos los eventos de la base de datos
    events = Evento.query.all()
    
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        user_id = request.form.get('user_id')
        if not event_id or not user_id:
            flash("Debes seleccionar un evento y escribir tu documento.", "warning")
            return redirect(url_for('consulta_qr'))
        return redirect(url_for('mostrar_qr', event_id=event_id, user_id=user_id))
    
    return render_template('consulta_qr.html', events=events)

# Ruta para mostrar el QR y los detalles del evento seleccionado
@app.route('/mostrar_qr/<int:event_id>/<string:user_id>')
def mostrar_qr(event_id, user_id):
    # Verificar inscripción en Asistentes o Participantes (lógica ya definida)
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
        flash("No estás registrado como Asistente ni Participante en este evento.", "danger")
        return redirect(url_for('consulta_qr'))
    
    # Preparar datos para el QR
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
    
    # Obtener el evento real desde la base de datos
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
        
        imagen_file = request.files.get("imagen")
        if imagen_file and imagen_file.filename != "":
            imagen_filename = save_image(imagen_file)
            if imagen_filename:
                evento.imagen = imagen_filename

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
    
    if evento.eve_estado == "CREADO":
        evento.eve_estado = "ACTIVO"
        db.session.commit()
        flash("El evento ha sido activado correctamente.", "success")
    else:
        flash("El evento ya está activo o en otro estado.", "warning")

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




# PUNTO DE ENTRADA
if __name__ == "__main__":
    app.run(debug=True)
