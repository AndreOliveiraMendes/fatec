from math import ceil
from flask import Blueprint, render_template, session, request
from markupsafe import Markup
from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string, get_data_reserva
from datetime import datetime
from config.general import LOCAL_TIMEZONE
from app.models import TipoAulaEnum
from app.auxiliar.dao import get_laboratorios, get_turnos, get_aulas_ativas_reservas_dia
from app.models import db, Turnos, Reservas_Fixas, Reservas_Temporarias, Semestres
from sqlalchemy import select, between
from sqlalchemy.exc import MultipleResultsFound

bp = Blueprint('consultar_reservas', __name__, url_prefix="/consultar_reserva")

def get_reserva(lab, aula, dia):
    try:
        fixa, temp = None, None
        sel_semestre = select(Semestres).where(
            between(dia, Semestres.data_inicio, Semestres.data_fim)
        )
        semestre = db.session.execute(sel_semestre).scalar_one_or_none()
        if semestre:
            sel_fixa = select(Reservas_Fixas).where(
                Reservas_Fixas.id_reserva_laboratorio == lab,
                Reservas_Fixas.id_reserva_aula == aula,
                Reservas_Fixas.id_reserva_semestre == semestre.id_semestre
            )
            fixa = db.session.execute(sel_fixa).scalar_one_or_none()
        sel_temp = select(Reservas_Temporarias).where(
            Reservas_Temporarias.id_reserva_laboratorio == lab,
            Reservas_Temporarias.id_reserva_aula == aula,
            between(dia, Reservas_Temporarias.inicio_reserva, Reservas_Temporarias.fim_reserva)
        )
        temp = db.session.execute(sel_temp).scalar_one_or_none()
        data = ""
        if temp or fixa:
            if temp:
                data += get_data_reserva(temp, prefix = None)
            else:
                data += get_data_reserva(fixa, prefix = None)
        else:
            data += "Livre"
        return Markup(data)
    except MultipleResultsFound as e:
        return f"not ok:{e}"

def divide(l, q):
    result = []
    qt = len(l)
    for g in range(ceil(qt/q)):
        result.append([])
        for i in range(q*g, min(q*(g+1), len(l))):
            result[-1].append(l[i])
    return result

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
    extras['get_reserva'] = get_reserva
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
    return render_template("reserva/televisor.html", username=username, perm=perm, **extras)