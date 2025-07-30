from flask import Blueprint, render_template, session, request
from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string
from datetime import datetime
from config.general import LOCAL_TIMEZONE
from app.models import TipoAulaEnum
from app.auxiliar.dao import get_laboratorios, get_turnos

bp = Blueprint('consultar_reservas', __name__, url_prefix="/consultar_reserva")

@bp.route('/')
def main_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'dia':today}
    reserva_dia = request.args.get('reserva-dia', default=today.date().strftime("%Y-%m-%d"))
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario')
    extras['laboratorios'] = get_laboratorios(True, True)
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    extras['reserva_dia'] = parse_date_string(reserva_dia)
    extras['reserva_turno'] = reserva_turno
    extras['reserva_tipo_horario'] = reserva_tipo_horario
    return render_template("reserva/main.html", username=username, perm=perm, **extras)