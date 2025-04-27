from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db  # Aquí 

migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)        # Inicializar la base de datos
    migrate.init_app(app, db)

    # Registra Blueprints
    from blueprints.main        import main_bp
    from blueprints.eventos      import eventos_bp
    from blueprints.registros import registros_bp
    from blueprints.participantes import participantes_bp
    from blueprints.qr          import qr_bp
    from blueprints.admin       import admin_bp
    from blueprints.super_admin  import super_admin_bp
    from blueprints.evaluadores  import evaluadores_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(eventos_bp)
    app.register_blueprint(registros_bp)
    app.register_blueprint(participantes_bp)
    app.register_blueprint(qr_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(evaluadores_bp)

    return app

if __name__ == "__main__":
    create_app().run(debug=True)
