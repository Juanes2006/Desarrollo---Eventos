from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import ENUM

db = SQLAlchemy()


# PARA MIGRAR LA BASE DE DATOS, DESCOMENTAR LAS SIGUIENTES LINEAS Y EJECUTAR EN LA TERMINAL:
#flask db init -> EN ESTE CASO NO SE NECESITA PORQUE YA ESTA INICIALIZADA
#flask db migrate -m "Agregando tablas"
#flask db upgrade



class AdministradorEvento(db.Model):
    __tablename__ = 'administradores_evento'
    adm_id = db.Column(db.String(20), primary_key=True)
    adm_nombre = db.Column(db.String(100))
    adm_correo = db.Column(db.String(100))
    adm_telefono = db.Column(db.String(45))
    eventos = db.relationship("Evento", backref="administrador")

class Area(db.Model):
    __tablename__ = 'areas'
    are_codigo = db.Column(db.Integer, primary_key=True)
    are_nombre = db.Column(db.String(45))
    are_descripcion = db.Column(db.String(400))
    categorias = db.relationship("Categoria", backref="area")

class Categoria(db.Model):
    __tablename__ = 'categorias'
    cat_codigo = db.Column(db.Integer, primary_key=True)
    cat_nombre = db.Column(db.String(45))
    cat_descripcion = db.Column(db.String(400))
    cat_area_fk = db.Column(db.Integer, db.ForeignKey('areas.are_codigo'))

class EventoCategoria(db.Model):
    __tablename__ = 'eventos_categorias'
    eve_cat_evento_fk = db.Column(db.Integer, db.ForeignKey('eventos.eve_id'), primary_key=True)
    eve_cat_categoria_fk = db.Column(db.Integer, db.ForeignKey('categorias.cat_codigo'), primary_key=True)

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
    cobro = db.Column(db.String(2), nullable=False, default="No")
    cupos = db.Column(db.Integer, nullable=True)
    imagen = db.Column(db.String(255), nullable=True)
    archivo_programacion = db.Column(db.String(255), nullable=True)
    inscripciones_participantes_abiertas = db.Column(db.Boolean, default=True)
    inscripciones_asistentes_abiertas = db.Column(db.Boolean, default=True)
    categorias = db.relationship('Categoria', secondary='eventos_categorias', backref='eventos')

class Asistentes(db.Model):
    __tablename__ = 'asistentes'
    asi_id = db.Column(db.String(20), primary_key=True)
    asi_nombre = db.Column(db.String(100))
    asi_correo = db.Column(db.String(100))
    asi_telefono = db.Column(db.String(20))
    asistentes_eventos = db.relationship('AsistentesEventos', backref='asistente', lazy=True)

class AsistentesEventos(db.Model):
    __tablename__ = 'asistentes_eventos'
    asi_eve_asistente_fk = db.Column(db.String(20), db.ForeignKey('asistentes.asi_id'), primary_key=True)
    asi_eve_evento_fk = db.Column(db.Integer, db.ForeignKey('eventos.eve_id'), primary_key=True)
    asi_eve_fecha_hora = db.Column(db.DateTime)
    asi_eve_soporte = db.Column(db.String(255), nullable=True)
    asi_eve_estado = db.Column(db.String(45))
    asi_eve_clave = db.Column(db.String(45))

class Participantes(db.Model):
    __tablename__ = 'participantes'
    par_id = db.Column(db.String(20), primary_key=True)
    par_nombre = db.Column(db.String(100))
    par_correo = db.Column(db.String(100))
    par_telefono = db.Column(db.String(45))
    participantes_eventos = db.relationship('ParticipantesEventos', backref='participante', lazy=True)
    calificaciones = db.relationship('Calificacion', backref='participante', lazy=True)

class ParticipantesEventos(db.Model):
    __tablename__ = 'participantes_eventos'
    par_eve_participante_fk = db.Column(db.String(20), db.ForeignKey('participantes.par_id'), primary_key=True)
    par_eve_evento_fk = db.Column(db.Integer, db.ForeignKey('eventos.eve_id'), primary_key=True)
    par_eve_fecha_hora = db.Column(db.DateTime)
    par_eve_documentos = db.Column(db.String(255), nullable=True)
    par_eve_or = db.Column(db.String(255), nullable=True)
    par_eve_clave = db.Column(db.String(45))
    par_estado = db.Column(ENUM('PENDIENTE', 'ACEPTADO', 'RECHAZADO'), nullable=False, default='PENDIENTE')
    


class Criterio(db.Model):
    __tablename__ = 'criterios'
    cri_id = db.Column(db.Integer, primary_key=True)
    cri_descripcion = db.Column(db.String(100), nullable=False)
    cri_peso = db.Column(db.Float, nullable=False)
    cri_evento_fk = db.Column(db.Integer, nullable=False)

    # Relación con Calificaciones
    calificaciones = db.relationship('Calificacion', backref='criterio', lazy=True)




class Evaluador(db.Model):
    __tablename__ = 'evaluadores'
    eva_id = db.Column(db.String(20), primary_key=True)
    eva_nombre = db.Column(db.String(100), nullable=False)
    eva_correo = db.Column(db.String(100), nullable=False)
    eva_telefono = db.Column(db.String(45), nullable=False)

    # Relación con Calificaciones
    calificaciones = db.relationship('Calificacion', backref='evaluador', lazy=True)


class Calificacion(db.Model):
    __tablename__ = 'calificaciones'
    id = db.Column(db.Integer, primary_key=True)  # Es buena práctica tener un id interno en la tabla
    cal_evaluador_fk = db.Column(db.String(20), db.ForeignKey('evaluadores.eva_id'), nullable=False)
    cal_criterio_fk = db.Column(db.Integer, db.ForeignKey('criterios.cri_id'), nullable=False)
    cal_participante_fk = db.Column(db.String(20), db.ForeignKey('participantes.par_id'), nullable=False)
    cal_valor = db.Column(db.Integer, nullable=False)