from flask import Blueprint, flash, session, render_template, request
from app.auxiliar.auxiliar_routes import get_user_info

bp = Blueprint('reservas_semanais', __name__, url_prefix="/reserva_fixa")

@bp.route('/')
def main_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)

    return render_template('reserva_fixa/main.html', username=username, perm=perm)