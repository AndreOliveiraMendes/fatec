import os

from dotenv import load_dotenv
from tzlocal import get_localzone


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def str_to_bool(s):
    return str(s).lower() in ['true', '1', 'yes', 'on']


# --------------------------------------------------
# Environment loading
# --------------------------------------------------

load_dotenv(".env")

ENV_MODE = os.getenv("FLASK_ENV", "dev")  # Default: dev
load_dotenv(f".env.{ENV_MODE}")


# --------------------------------------------------
# Flask config
# --------------------------------------------------

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    HOST = os.getenv("MYSQL_HOST")
    PORT = os.getenv("MYSQL_PORT")
    USER = os.getenv("MYSQL_USER")
    PASSWORD = os.getenv("MYSQL_PASSWORD")
    DATABASE = os.getenv("MYSQL_DATABASE")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    )

    DEBUG = str_to_bool(os.getenv("FLASK_DEBUG", "False"))


def get_config():
    return Config


# --------------------------------------------------
# Debug / erros
# --------------------------------------------------

SHOW_DEBUG_ERRORS = str_to_bool(os.getenv("SHOW_DEBUG_ERRORS", "False"))
LIST_ROUTES = str_to_bool(os.getenv("LIST_ROUTES", "False"))


# --------------------------------------------------
# MySQL
# --------------------------------------------------

AUTO_CREATE_MYSQL = str_to_bool(os.getenv("AUTO_CREATE_MYSQL", "False"))


# --------------------------------------------------
# API
# --------------------------------------------------

API_BASIC_PROTOCOL = os.getenv("API_BASIC_PROTOCOL", os.getenv("TOMCAT_PROTOCOL", "http"))
API_BASIC_HOST = os.getenv("API_BASIC_HOST", os.getenv("TOMCAT_HOST", "127.0.0.1"))
API_BASIC_PORT = os.getenv("API_BASIC_PORT", os.getenv("TOMCAT_PORT"))

# checks for accidental None values from env
if API_BASIC_PORT:
    API_BASIC_PORT = API_BASIC_PORT.strip().lower()
    if API_BASIC_PORT in ("none", "null"):
        API_BASIC_PORT = None

API_FINAL_PORT = f":{API_BASIC_PORT}" if API_BASIC_PORT else ""
API_BASIC_URL = f"{API_BASIC_PROTOCOL}://{API_BASIC_HOST}{API_FINAL_PORT}/autenticar/json"

API_BASIC_USER = os.getenv("API_BASIC_USER")
API_BASIC_PASS = os.getenv("API_BASIC_PASS")


# --------------------------------------------------
# CRUD
# --------------------------------------------------

PER_PAGE = int(os.getenv("PER_PAGE", "10"))
AFTER_ACTION = os.getenv("AFTER_ACTION", "noredirect")


# --------------------------------------------------
# Flask runtime
# --------------------------------------------------

FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))


# --------------------------------------------------
# Datetime
# --------------------------------------------------

LOCAL_TIMEZONE = get_localzone()
FIRST_DAY_OF_WEEK = os.getenv("FIRST_DAY_OF_WEEK", "domingo")
INDEX_START = int(os.getenv("INDEX_START", "0"))


# --------------------------------------------------
# Disponibilidade DB
# --------------------------------------------------

DISPONIBILIDADE_HOST = os.getenv("DISPONIBILIDADE_HOST")
DISPONIBILIDADE_USER = os.getenv("DISPONIBILIDADE_USER")
DISPONIBILIDADE_PASSWORD = os.getenv("DISPONIBILIDADE_PASSWORD")
DISPONIBILIDADE_DATABASE = os.getenv("DISPONIBILIDADE_DATABASE")


# --------------------------------------------------
# Acadêmico DB
# --------------------------------------------------

ACADEMICO_HOST = os.getenv("ACADEMICO_HOST")
ACADEMICO_USER = os.getenv("ACADEMICO_USER")
ACADEMICO_PASSWORD = os.getenv("ACADEMICO_PASSWORD")
ACADEMICO_DATABASE = os.getenv("ACADEMICO_DATABASE")