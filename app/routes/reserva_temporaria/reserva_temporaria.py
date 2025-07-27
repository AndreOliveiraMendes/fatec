from flask import Blueprint, flash, session, render_template, redirect, url_for, request, abort
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from datetime import date, datetime
from app.models import db, TipoAulaEnum, Turnos
from app.auxiliar.auxiliar_routes import get_user_info, registrar_log_generico_usuario, parse_date_string, \
    time_range, none_if_empty
from app.auxiliar.dao import get_turnos, get_aulas_ativas_reservas_dias
from collections import Counter

bp = Blueprint('reservas_esporádicas', __name__, url_prefix="/reserva_temporaria")

@bp.route('/', methods=['GET', 'POST'])
def main_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'GET':
        today = date.today()
        extras['day'] = today
        return render_template('reserva_temporaria/main.html', username=username, perm=perm, **extras)
    else:
        dia_inicial = parse_date_string(request.form.get('dia_inicio'))
        dia_final = parse_date_string(request.form.get('dia_fim'))
        if not dia_inicial or not dia_final:
            abort(400)
        if dia_inicial > dia_final:
            dia_inicial, dia_final = dia_final, dia_inicial
        days = [day for day in time_range(dia_inicial, dia_final)]
        extras['tipo_aula'] = TipoAulaEnum
        extras['dias'] = days
        extras['turnos'] = get_turnos()
        return render_template('reserva_temporaria/dias.html', username=username, perm=perm, **extras)

@bp.route('/dias', methods=['POST'])
def process_turnos():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    tipo_horario = none_if_empty(request.form.get('tipo_horario'))
    if not tipo_horario:
        abort(400)
    tipo_aula = TipoAulaEnum(tipo_horario)
    brute_chks = [(key.replace('info[', '').replace(']', '').split(',')) for key, value in request.form.items() if 'info' in key and value == 'on']
    chks = [(parse_date_string(chk[0]), db.get_or_404(Turnos, chk[1])) for chk in brute_chks]
    aulas_ativas = get_aulas_ativas_reservas_dias(chks, tipo_aula)
    extras['aulas_ativas'] = aulas_ativas
    return render_template('reserva_temporaria/turnos.html', username=username, perm=perm, **extras)