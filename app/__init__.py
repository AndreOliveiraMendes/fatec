import os

from flask import Flask

from app.auxiliar import template
from app.extensions import db
from app.routes import register_blueprints
from app.types import url_custom_types
from config.general import AUTO_CREATE_MYSQL, get_config
from config.logging_config import setup_logging
import sass


def create_app(name=None):
    name = name if name else __name__
    app = Flask(name)
    app.config.from_object(get_config())
    db.init_app(app)

    setup_logging(app)
    
    scss_dir = os.path.join(app.root_path, 'static', 'scss')
    css_dir = os.path.join(app.root_path, 'static', 'css')

    os.makedirs(css_dir, exist_ok=True)

    sass.compile(
        dirname=(scss_dir, css_dir),
        output_style='compressed'
    )

    app.logger.debug("[SCSS] compilado")

    with app.app_context():
        from app.auxiliar import error
        template.register_template_utils(app)
        error.register_error_handler(app)
        url_custom_types.registrar_custom_url_type(app)

        register_blueprints(app)

        if AUTO_CREATE_MYSQL:
            db.create_all()
    
    #sessao
    #app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    #app.config.update(
    #    SESSION_COOKIE_HTTPONLY=not app.debug,
    #    SESSION_COOKIE_SECURE=not app.debug,
    #    SESSION_COOKIE_SAMESITE="Lax"
    #)

    return app
