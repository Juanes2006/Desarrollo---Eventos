import os

class Config:
    SECRET_KEY = "clave_secreta_para_flash"
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/eventos_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Carpetas de uploads
    UPLOAD_FOLDER_IMAGENES      = os.path.join(os.getcwd(), 'static', 'imagenes')
    UPLOAD_FOLDER_PAGOS         = os.path.join(os.getcwd(), 'static', 'uploads')
    UPLOAD_FOLDER_PROGRAMACION  = os.path.join(os.getcwd(), 'static', 'programacion')
    # Permisos
    ALLOWED_EXTENSIONS_IMAGENES     = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_EXTENSIONS_PAGOS        = {'png', 'jpg', 'jpeg', 'pdf'}
    ALLOWED_EXTENSIONS_PROGRAMACION = {'pdf'}
                                