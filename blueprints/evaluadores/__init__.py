from flask import Blueprint
evaluador_bp = Blueprint('evaluador', __name__, url_prefix='/evaluador', template_folder='../../templates/evaluador')
from models import db, Evaluador, Criterio, Calificacion, ParticipantesEventos, Participantes, AsistentesEventos, Asistentes, Evento
from . import routes
