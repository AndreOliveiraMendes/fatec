import logging
import os
from logging.handlers import TimedRotatingFileHandler

from flask import Flask

from app.extensions import Base, db
from app.routes import register_blueprints
from config.general import AUTO_CREATE_MYSQL, get_config


def create_app(name=None):
    name = name if name else __name__
    app = Flask(name)
    app.config.from_object(get_config())
    db.init_app(app)

    configure_logging(app)

    with app.app_context():
        from app.auxiliar import auxiliar_template, error, url_custom_types
        auxiliar_template.register_filters(app)
        error.register_error_handler(app)
        url_custom_types.registrar_custom_url_type(app)

        register_blueprints(app)

        if AUTO_CREATE_MYSQL:
            db.create_all()

    return app

def configure_logging(app):
    if not os.path.exists('logs'):
        os.makedirs('logs')
    #handler = logging.FileHandler('logs/app.log')
    handler = TimedRotatingFileHandler(
        filename='logs/app.log',
        when='midnight',   # gira o arquivo todo dia à meia-noite
        interval=1,        # a cada 1 unidade do "when"
        backupCount=90,  # mantém só X dias de log
        encoding='utf-8'
    )
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)