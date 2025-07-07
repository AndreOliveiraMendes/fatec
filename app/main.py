from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import get_config

app = Flask(__name__)
app.config.from_object(get_config())
db:SQLAlchemy = SQLAlchemy(app)

from app.routes import *
from app.auxiliar.auxiliar_template import *

if __name__ == "__main__":
    app.run()