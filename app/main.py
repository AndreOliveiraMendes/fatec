import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import get_config
from app.routes import register_blueprints
from app.extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())
    db.init_app(app)

    with app.app_context():
        register_blueprints(app)
        from app.auxiliar import auxiliar_template
        from app.auxiliar import error
        auxiliar_template.register_filters(app)
        error.register_error_handler(app)

        if os.getenv("AUTO_CREATE_DB") == "True":
            db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
