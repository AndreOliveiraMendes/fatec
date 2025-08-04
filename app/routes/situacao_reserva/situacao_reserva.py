from flask import Blueprint, render_template, session, request
from datetime import datetime
from app.models import db, Turnos, Reservas_Fixas, Reservas_Temporarias
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string
from app.auxiliar.dao import get_reservas_por_dia, get_turnos, get_situacoes_por_dia, check_first

bp = Blueprint('situacao_reserva', __name__, url_prefix="/status_reserva")

@bp.route('/')
@admin_required
def gerenciar_status():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    hoje = datetime.today()
    extras = {'hoje':hoje}
    reserva_dia = parse_date_string(request.args.get('reserva-dia', default=hoje.date().strftime("%Y-%m-%d")))
    reserva_turno = request.args.get('reserva_turno', type=int)
    extras['turnos'] = get_turnos()
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    turno = None
    if reserva_turno is not None:
        turno = db.session.get(Turnos, reserva_turno)
    if not reserva_dia:
        reserva_dia = hoje.date()
    reservas_fixas, reservas_temporarias = get_reservas_por_dia(reserva_dia, turno)
    reservas = []
    i, j, control_1, control_2 = 0, 0, len(reservas_fixas), len(reservas_temporarias)
    while i < control_1 or j < control_2:
        reserva = {}
        if i < control_1 and j < control_2:
            rf = reservas_fixas[i]
            rt = reservas_temporarias[j]
            who = check_first(rf, rt)
            if who == 0:
                reserva['horario'] = rf.aulas_ativas
                reserva['laboratorio'] = rf.laboratorios
                reserva['fixa'] = rf
                reserva['temporaria'] = None
                i += 1
            elif who == 1:
                reserva['horario'] = rt.aulas_ativas
                reserva['laboratorio'] = rt.laboratorios
                reserva['fixa'] = None
                reserva['temporaria'] = rt
                j += 1
            else:
                reserva['horario'] = rf.aulas_ativas
                reserva['laboratorio'] = rf.laboratorios
                reserva['fixa'] = rf
                reserva['temporaria'] = rt
                i += 1
                j += 1
        elif i < control_1:
            rf = reservas_fixas[i]
            reserva['horario'] = rf.aulas_ativas
            reserva['laboratorio'] = rf.laboratorios
            reserva['fixa'] = rf
            reserva['temporaria'] = None
            i += 1
        else:
            rt = reservas_temporarias[j]
            reserva['horario'] = rt.aulas_ativas
            reserva['laboratorio'] = rt.laboratorios
            reserva['fixa'] = None
            reserva['temporaria'] = rt
            j += 1
        situacao = get_situacoes_por_dia(reserva['horario'], reserva['laboratorio'], reserva_dia)
        reserva['situacao'] = situacao
        reservas.append(reserva)
    extras['reservas'] = reservas
    return render_template("status_reserva/status_reserva.html", username=username, perm=perm, **extras)