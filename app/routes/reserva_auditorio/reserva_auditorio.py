from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from datetime import datetime
from config.general import LOCAL_TIMEZONE

from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import get_auditorios, get_reservas_auditorios
from app.auxiliar.decorators import reserva_auditorio_required
from app.models import Reservas_Auditorios

bp = Blueprint('reservas_auditorios', __name__, url_prefix="/reserva_auditorio")

@bp.route('/')
@reserva_auditorio_required
def main_page():
    userid = session.get('userid')
    user = get_user_info(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'dia':today}
    extras['auditorios'] = get_auditorios()

    reserva_dia = parse_date_string(request.args.get('reserva-dia'))
    if not 'reserva-dia' in request.args:
        reserva_dia = today.date()
    extras['reserva_dia'] = reserva_dia

    conditions = []
    if reserva_dia:
        conditions.append(Reservas_Auditorios.dia_reserva == reserva_dia)
    extras['reservas_auditorios'] = get_reservas_auditorios(user.pessoa.id_pessoa, user.perm&PERM_ADMIN, *conditions)
    return render_template('reserva_auditorio/main.html', user=user, **extras)