from flask import Blueprint
registros_bp = Blueprint('registros', __name__, url_prefix='/eventos', template_folder='../../templates/registrations')
from . import routes

