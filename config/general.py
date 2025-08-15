import os

from dotenv import load_dotenv
from tzlocal import get_localzone


def str_to_bool(s):
    return str(s).lower() in ['true', '1', 'yes', 'on']

load_dotenv('.env')
ENV_MODE = os.getenv('FLASK_ENV', 'dev')  # Default: dev

load_dotenv(f'.env.{ENV_MODE}')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    HOST = os.getenv('MYSQL_HOST')
    PORT = os.getenv('MYSQL_PORT')
    USER = os.getenv('MYSQL_USER')
    PASSWORD = os.getenv('MYSQL_PASSWORD')
    DATABASE = os.getenv('MYSQL_DATABASE')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    DEBUG = os.getenv('FLASK_DEBUG', 'False')

def get_config():
    return Config

# Variáveis extras
# erros
SHOW_DEBUG_ERRORS = str_to_bool(os.getenv("SHOW_DEBUG_ERRORS", "False"))

# mysql database
AUTO_CREATE_MYSQL = str_to_bool(os.getenv("AUTO_CREATE_MYSQL", "False"))

# api
TOMCAT_PROTOCOL = os.getenv("TOMCAT_PROTOCOL", "http")
TOMCAT_HOST = os.getenv("TOMCAT_HOST", "127.0.0.1")
TOMCAT_PORT = os.getenv("TOMCAT_PORT", "5001")
TOMCAT_API_URL = f"{TOMCAT_PROTOCOL}://{TOMCAT_HOST}:{TOMCAT_PORT}/autenticar/json"
API_BASIC_USER = os.getenv("API_BASIC_USER")
API_BASIC_PASS = os.getenv("API_BASIC_PASS")

# crude related
PER_PAGE = int(os.getenv("PER_PAGE", "10"))
AFTER_ACTION = os.getenv("AFTER_ACTION", "noredirect")
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

# datatime related
LOCAL_TIMEZONE = get_localzone()
FIRST_DAY_OF_WEEK = os.getenv('FIRST_DAY_OF_WEEK', 'domingo')
INDEX_START = int(os.getenv('INDEX_START', '0'))

# disponibilidade
DISPONIBILIDADE_HOST = os.getenv('DISPONIBILIDADE_HOST')
DISPONIBILIDADE_USER = os.getenv('DISPONIBILIDADE_USER')
DISPONIBILIDADE_PASSWORD = os.getenv('DISPONIBILIDADE_PASSWORD')
DISPONIBILIDADE_DATABASE = os.getenv('DISPONIBILIDADE_DATABASE')