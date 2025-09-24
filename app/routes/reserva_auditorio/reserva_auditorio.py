from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)

from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import get_auditorios, get_reservas_auditorios
from app.auxiliar.decorators import reserva_auditorio_required

bp = Blueprint('reservas_auditorios', __name__, url_prefix="/reserva_auditorio")

@bp.route('/')
@reserva_auditorio_required
def main_page():
    userid = session.get('userid')
    user = get_user_info(userid)
    extras = {}
    extras['auditorios'] = get_auditorios()
    extras['reservas_auditorios'] = get_reservas_auditorios(user.pessoa.id_pessoa, user.perm&PERM_ADMIN)
    return render_template('reserva_auditorio/main.html', user=user, **extras)