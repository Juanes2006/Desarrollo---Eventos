from flask import Blueprint
participantes_bp = Blueprint('participantes', __name__, url_prefix='/participante', template_folder='../../templates/participants')
from . import routes
