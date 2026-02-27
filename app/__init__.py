import logging
import os
from logging.handlers import TimedRotatingFileHandler

from flask import Flask

from app.extensions import db
from app.routes import register_blueprints
from app.types import url_custom_types
from config.general import AUTO_CREATE_MYSQL, get_config


def create_app(name=None):
    name = name if name else __name__
    app = Flask(name)
    app.config.from_object(get_config())
    db.init_app(app)

    configure_logging(app)
    
    scss_dir = os.path.join(app.root_path, 'static', 'scss')
    css_dir = os.path.join(app.root_path, 'static', 'css')
    if app.debug:
        from flask_scss import Scss

        Scss(
            app,
            asset_dir=scss_dir,
            static_dir=css_dir
        )

        app.logger.debug("[SCSS] Compilação automática ativada (modo dev)")
    else:
        import sass

        os.makedirs(css_dir, exist_ok=True)

        sass.compile(
            dirname=(scss_dir, css_dir),
            output_style='compressed'
        )

        app.logger.debug("[SCSS] Compilado para produção")

    with app.app_context():
        from app.auxiliar import auxiliar_template, error
        auxiliar_template.register_filters(app)
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

def configure_logging(app):
    if not os.path.exists("logs"):
        os.makedirs("logs")

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # -------------------------
    # LOG PRINCIPAL DA APP
    # -------------------------
    app_handler = TimedRotatingFileHandler(
        "logs/app.log",
        when="midnight",
        interval=1,
        backupCount=90,
        encoding="utf-8"
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)

    app.logger.addHandler(app_handler)
    app.logger.setLevel(logging.INFO)

    # -------------------------
    # LOG DE COMANDOS
    # -------------------------
    cmd_handler = TimedRotatingFileHandler(
        "logs/commands.log",
        when="midnight",
        interval=1,
        backupCount=180,  # auditoria normalmente precisa mais retenção
        encoding="utf-8"
    )
    cmd_handler.setLevel(logging.INFO)
    cmd_handler.setFormatter(formatter)

    cmd_logger = logging.getLogger("commands")
    cmd_logger.setLevel(logging.INFO)
    cmd_logger.addHandler(cmd_handler)

    # evita duplicação no console/root logger
    cmd_logger.propagate = False

    # deixa disponível globalmente
    app.cmd_logger = cmd_logger