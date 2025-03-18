from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "clave_secreta_para_flash"

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
    ##opcionales
    cobro = db.Column(db.Float, nullable=True)
    cupos = db.Column(db.Integer, nullable=True)
    
    # Relaciones muchos-a-muchos
    categorias = db.relationship('Categoria', secondary='eventos_categorias', backref='eventos')

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
    evento = Evento.query.get_or_404(eve_id)

    return render_template("detalle_evento.html", evento=evento)

# HU50: Crear un nuevo evento
@app.route("/administrador/crear_evento", methods=["GET", "POST"])
def crear_evento():
    if request.method == "POST":
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
            cobro = float(cobro_str) if cobro_str else None
            cupos = int(cupos_str) if cupos_str else None

            # Obtén la categoría seleccionada
            # Si usas un select único, se utiliza get()
            categoria_id = request.form.get("categorias")
            # Si el campo es múltiple, usa getlist:
            # categoria_ids = request.form.getlist("categorias")

            admin_demo = AdministradorEvento.query.first()
            if not admin_demo:
                admin_demo = AdministradorEvento(
                    adm_id="admin1", 
                    adm_nombre="Juan Esteban M", 
                    adm_correo="Juanes@admin.com",
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
                cupos=cupos
            )
            db.session.add(nuevo_evento)
            db.session.commit()

            # Asocia la categoría seleccionada al evento, si se eligió alguna
            if categoria_id:
                categoria = Categoria.query.get(categoria_id)
                if categoria:
                    nuevo_evento.categorias.append(categoria)
                    db.session.commit()

            flash(f"¡Se ha creado un nuevo evento: {nuevo_evento.eve_nombre}!", "success")
            return redirect(url_for("super_adm"))

    # Para el método GET, además de los eventos, obtenemos las categorías para el select
    categorias = Categoria.query.all()
    eventos = Evento.query.all()  # Si deseas mostrarlos en la vista
    return render_template("crear_evento.html", eventos=eventos, categorias=categorias)





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
