from datetime import datetime, time
from math import ceil

from flask import Blueprint, render_template, request, session
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound

from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string
from app.auxiliar.dao import (get_aulas_ativas_por_dia, get_laboratorios,
                              get_turnos)
from app.models import TipoAulaEnum, Turnos, db
from config.general import LOCAL_TIMEZONE

bp = Blueprint('consultar_reservas', __name__, url_prefix="/consultar_reserva")

def divide(l, q):
    result = []
    qt = len(l)
    for g in range(ceil(qt/q)):
        result.append([])
        for i in range(q*g, min(q*(g+1), len(l))):
            result[-1].append(l[i])
    return result

def get_turno_by_time(hora:time):
    try:
        return db.session.execute(
            select(Turnos).where(
                Turnos.horario_inicio <= hora,
                hora <= Turnos.horario_fim
            )
        ).scalar_one_or_none()
    except MultipleResultsFound as e:
        return None

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
    if not reserva_dia:
        reserva_dia = today.date()
    turno = db.session.get(Turnos, reserva_turno) if reserva_turno is not None else None
    aulas = get_aulas_ativas_por_dia(reserva_dia, turno, TipoAulaEnum(reserva_tipo_horario))
    laboratorios = get_laboratorios(True, True)
    if len(aulas) == 0 or len(laboratorios) == 0:
        extras['skip'] = True
    extras['aulas'] = aulas
    extras['laboratorios'] = laboratorios
    return render_template("reserva/main.html", username=username, perm=perm, **extras)

@bp.route("/configurar")
def configurar_tela_televisor():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    extras['tipo_aula'] = TipoAulaEnum
    return render_template("reserva/televisor_control.html", username=username, perm=perm, **extras)

@bp.route("/televisor")
def tela_televisor():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    intervalo = request.args.get('intervalo', type=int)
    qt_lab = request.args.get('qt_lab', default=5, type=int)
    lab = divide(get_laboratorios(), qt_lab)
    extras['intervalo'] = intervalo*1000
    extras['laboratorios'] = lab
    today = datetime.now(LOCAL_TIMEZONE)
    extras['hoje'] = today
    turno = get_turno_by_time(today.time())
    aulas = get_aulas_ativas_por_dia(today.date(), turno, TipoAulaEnum(tipo_horario))
    extras['aulas'] = aulas
    return render_template("reserva/televisor.html", username=username, perm=perm, **extras)