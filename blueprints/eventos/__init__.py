from flask import Blueprint
eventos_bp = Blueprint('eventos', __name__, url_prefix='/administrador', template_folder='../../templates/events')
from . import routes


