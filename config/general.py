import os

from dotenv import load_dotenv
from tzlocal import get_localzone

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def str_to_bool(s):
    return str(s).lower() in ("true", "1", "yes", "on")


def env(key, default=None, cast=None):
    value = os.getenv(key, default)

    if cast and value is not None:
        value = cast(value)

    return value


# --------------------------------------------------
# Environment loading
# --------------------------------------------------

load_dotenv(".env")

ENV_MODE = env("FLASK_ENV", "dev")
load_dotenv(f".env.{ENV_MODE}")


# --------------------------------------------------
# Flask config
# --------------------------------------------------

class Config:
    SECRET_KEY = env("SECRET_KEY")

    HOST = env("MYSQL_HOST")
    PORT = env("MYSQL_PORT")
    USER = env("MYSQL_USER")
    PASSWORD = env("MYSQL_PASSWORD")
    DATABASE = env("MYSQL_DATABASE")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    )

    DEBUG = env("FLASK_DEBUG", False, str_to_bool)


def get_config():
    return Config


# --------------------------------------------------
# Debug / erros
# --------------------------------------------------

SHOW_DEBUG_ERRORS = env("SHOW_DEBUG_ERRORS", False, str_to_bool)
LIST_ROUTES = env("LIST_ROUTES", False, str_to_bool)


# --------------------------------------------------
# MySQL
# --------------------------------------------------

AUTO_CREATE_MYSQL = env("AUTO_CREATE_MYSQL", False, str_to_bool)


# --------------------------------------------------
# API
# --------------------------------------------------

API_BASIC_PROTOCOL = env("API_BASIC_PROTOCOL", env("TOMCAT_PROTOCOL", "http"))
API_BASIC_HOST = env("API_BASIC_HOST", env("TOMCAT_HOST", "127.0.0.1"))
API_BASIC_PORT = env("API_BASIC_PORT", env("TOMCAT_PORT"))

if API_BASIC_PORT:
    API_BASIC_PORT = API_BASIC_PORT.strip().lower()
    if API_BASIC_PORT in ("none", "null"):
        API_BASIC_PORT = None

API_FINAL_PORT = f":{API_BASIC_PORT}" if API_BASIC_PORT else ""
API_BASIC_URL = f"{API_BASIC_PROTOCOL}://{API_BASIC_HOST}{API_FINAL_PORT}/autenticar/json"

API_BASIC_USER = env("API_BASIC_USER")
API_BASIC_PASS = env("API_BASIC_PASS")


# --------------------------------------------------
# CRUD
# --------------------------------------------------

PER_PAGE = env("PER_PAGE", 10, int)
AFTER_ACTION = env("AFTER_ACTION", "noredirect")


# --------------------------------------------------
# Flask runtime
# --------------------------------------------------

FLASK_HOST = env("FLASK_HOST", "127.0.0.1")
FLASK_PORT = env("FLASK_PORT", 5000, int)


# --------------------------------------------------
# Datetime
# --------------------------------------------------

LOCAL_TIMEZONE = get_localzone()
FIRST_DAY_OF_WEEK = env("FIRST_DAY_OF_WEEK", "domingo")
INDEX_START = env("INDEX_START", 0, int)


# --------------------------------------------------
# Disponibilidade DB
# --------------------------------------------------

DISPONIBILIDADE_HOST = env("DISPONIBILIDADE_HOST")
DISPONIBILIDADE_USER = env("DISPONIBILIDADE_USER")
DISPONIBILIDADE_PASSWORD = env("DISPONIBILIDADE_PASSWORD")
DISPONIBILIDADE_DATABASE = env("DISPONIBILIDADE_DATABASE")


# --------------------------------------------------
# Acadêmico DB
# --------------------------------------------------

ACADEMICO_HOST = env("ACADEMICO_HOST")
ACADEMICO_USER = env("ACADEMICO_USER")
ACADEMICO_PASSWORD = env("ACADEMICO_PASSWORD")
ACADEMICO_DATABASE = env("ACADEMICO_DATABASE")