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
SHOW_DEBUG_ERRORS = str_to_bool(os.getenv("SHOW_DEBUG_ERRORS", "False"))
AUTO_CREATE_MYSQL = str_to_bool(os.getenv("AUTO_CREATE_MYSQL", "False"))
TOMCAT_HOST = os.getenv("TOMCAT_HOST", "127.0.0.1")
TOMCAT_PORT = os.getenv("TOMCAT_PORT", "5001")
TOMCAT_API_URL = f"http://{TOMCAT_HOST}:{TOMCAT_PORT}/api/autenticar/json"
API_BASIC_USER = os.getenv("API_BASIC_USER")
API_BASIC_PASS = os.getenv("API_BASIC_PASS")
PER_PAGE = int(os.getenv("PER_PAGE", "10"))
AFTER_ACTION = os.getenv("AFTER_ACTION", "noredirect")
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
LOCAL_TIMEZONE = get_localzone()