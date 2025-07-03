import os
from dotenv import load_dotenv

load_dotenv('.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    HOST = os.getenv('DB_HOST')
    PORT = os.getenv('DB_PORT')
    USER = os.getenv('DB_USER')
    PASSWORD = os.getenv('DB_PASSWORD')
    DATABASE = os.getenv('DB_DATABASE')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    DEBUG = os.getenv('FLASK_DEBUG')

def get_config():
    #TODO implement diferent environment variables
    #mode = os.getenv("FLASK_ENV")
    return Config

SHOW_DEBUG_ERRORS = "True" == os.getenv("SHOW_DEBUG_ERRORS", False)