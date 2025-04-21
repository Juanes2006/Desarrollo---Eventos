from flask import Blueprint
super_admin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin', template_folder='../../templates/superadmin')
from . import routes
