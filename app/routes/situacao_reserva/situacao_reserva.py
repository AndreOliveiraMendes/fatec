from flask import Blueprint, render_template, session, request
from datetime import datetime
from app.models import Reservas_Fixas, Reservas_Temporarias
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string
from app.auxiliar.dao import get_reservas_por_dia, get_turnos

bp = Blueprint('situacao_reserva', __name__, url_prefix="/status_reserva")

def check_first(reserva_fixa:Reservas_Fixas, reserva_temporaria:Reservas_Temporarias):
    if reserva_fixa.aulas_ativas.aulas.horario_inicio < reserva_temporaria.aulas_ativas.aulas.horario_inicio:
        return 0
    elif reserva_fixa.aulas_ativas.aulas.horario_inicio > reserva_temporaria.aulas_ativas.aulas.horario_inicio:
        return 1
    else:
        if reserva_fixa.id_reserva_laboratorio < reserva_temporaria.id_reserva_laboratorio:
            return 0
        elif reserva_fixa.id_reserva_laboratorio > reserva_temporaria.id_reserva_laboratorio:
            return 1
        else:
            return 2

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
    reservas_fixas, reservas_temporarias = get_reservas_por_dia(reserva_dia, reserva_turno)
    reservas = []
    i, j, control_1, control_2 = 0, 0, len(reservas_fixas), len(reservas_temporarias)
    while i < control_1 or j < control_2:
        if i < control_1 and j < control_2:
            rf = reservas_fixas[i]
            rt = reservas_temporarias[j]
            who = check_first(rf, rt)
            if who == 0:
                reservas.append({'horario':rf.aulas_ativas.aulas, 'laboratorio':rf.laboratorios, 'fixa':rf, 'temporaria':None})
                i += 1
            elif who == 1:
                reservas.append({'horario':rt.aulas_ativas.aulas, 'laboratorio':rt.laboratorios, 'fixa':None, 'temporaria':rt})
                j += 1
            else:
                reservas.append({'horario':rf.aulas_ativas.aulas, 'laboratorio':rf.laboratorios, 'fixa':rf, 'temporaria':rt})
                i += 1
                j += 1
        elif i < control_1:
            rf = reservas_fixas[i]
            reservas.append({'horario':rf.aulas_ativas.aulas, 'laboratorio':rf.laboratorios, 'fixa':rf, 'temporaria':None})
            i += 1
        else:
            rt = reservas_temporarias[j]
            reservas.append({'horario':rt.aulas_ativas.aulas, 'laboratorio':rt.laboratorios, 'fixa':None, 'temporaria':rt})
            j += 1
    extras['reservas'] = reservas
    return render_template("status_reserva/status_reserva.html", username=username, perm=perm, **extras)