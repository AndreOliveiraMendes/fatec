from flask import Blueprint, render_template, session, request, flash
from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string
from datetime import datetime
from config.general import LOCAL_TIMEZONE
from app.models import TipoAulaEnum
from app.auxiliar.dao import get_laboratorios, get_turnos, get_aulas_ativas_reservas_dia, Reservas_Fixas
from app.models import db, Turnos

bp = Blueprint('consultar_reservas', __name__, url_prefix="/consultar_reserva")

def get_reserva(lab, aula, dia):
    pass

@bp.route('/')
def main_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'dia':today}
    reserva_dia = parse_date_string(request.args.get('reserva-dia', default=today.date().strftime("%Y-%m-%d")))
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    extras['reserva_tipo_horario'] = reserva_tipo_horario

    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA.value
    turno = db.session.get(Turnos, reserva_turno) if reserva_turno is not None else None
    aulas = get_aulas_ativas_reservas_dia(reserva_dia, turno, TipoAulaEnum(reserva_tipo_horario))
    laboratorios = get_laboratorios(True, True)
    if len(aulas) == 0 or len(laboratorios) == 0:
        extras['skip'] = True
    extras['aulas'] = aulas
    extras['laboratorios'] = laboratorios
    return render_template("reserva/main.html", username=username, perm=perm, **extras)