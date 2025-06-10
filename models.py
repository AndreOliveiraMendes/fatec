import configparser
from main import app

config = configparser.ConfigParser()
config.read('config.ini')
config_dict = {section: dict(config.items(section)) for section in config.sections()}
config_dict['SECRET_KEY'] = config['DEFAULT']['SECRET_KEY']

print("ok")
print(config_dict)