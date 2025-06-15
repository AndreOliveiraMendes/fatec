from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import get_config

app = Flask(__name__)
app.config.from_object(get_config())
db = SQLAlchemy(app)

from routes.auth import *
from routes.default import *
from routes.error import *
from auxiliar_template.auxiliar import *

if __name__ == "__main__":
    app.run(debug=True)