import logging
import os

from flask import Flask

from app.extensions import db
from app.routes import register_blueprints
from config.general import AUTO_CREATE_MYSQL, get_config


def create_app():
    app = Flask(__name__)
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
    handler = logging.FileHandler('logs/app.log')
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)