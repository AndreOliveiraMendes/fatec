import configparser
from flask_sqlalchemy import SQLAlchemy
from main import app

config = configparser.ConfigParser()
config.read('config.ini')
config_dict = {section: dict(config.items(section)) for section in config.sections()}

app.config['SQLALCHEMY_DATABASE_URI'] = config_dict['database']['mysql_url']
app.config['SECRETS'] = config_dict['default']['secret_key']

db = SQLAlchemy(app)