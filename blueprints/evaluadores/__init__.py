from flask import Blueprint

evaluadores_bp = Blueprint(
    'evaluadores',                 # Nombre interno
    __name__,
    url_prefix='/evaluador',        # Prefijo para todas las rutas
    template_folder='../../templates/evaluador'  # Ajusta según tu estructura
)

from . import routes  # Este importa tus rutas
