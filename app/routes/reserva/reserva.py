from flask import Blueprint, render_template, session
from app.auxiliar.auxiliar_routes import get_user_info
from datetime import datetime
from config.general import LOCAL_TIMEZONE
from app.auxiliar.dao import get_laboratorios

bp = Blueprint('consultar_reservas', __name__, url_prefix="/consultar_reserva")

@bp.route('/')
def main_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'dia':today}
    extras['laboratorios'] = get_laboratorios(True, True)
    return render_template("reserva/main.html", username=username, perm=perm, **extras)