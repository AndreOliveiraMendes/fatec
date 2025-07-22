from app import create_app
from config.general import FLASK_HOST, FLASK_PORT
if __name__ == "__main__":
    app = create_app()
    app.run(host=FLASK_HOST, port=FLASK_PORT)