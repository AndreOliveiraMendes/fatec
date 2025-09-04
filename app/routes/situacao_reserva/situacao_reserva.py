from copy import copy
from datetime import datetime

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_unique_or_500, get_user_info,
                                          parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import (check_first, get_reservas_por_dia,
                              get_situacoes_por_dia, get_turno_by_time,
                              get_turnos)
from app.auxiliar.decorators import admin_required
from app.models import (SituacaoChaveEnum, Situacoes_Das_Reserva, TipoAulaEnum,
                        Turnos, db)

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
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    if not 'reserva_turno' in request.args:
        reserva_turno = get_turno_by_time(hoje.time())
        if reserva_turno:
            reserva_turno = reserva_turno.id_turno
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    extras['reserva_tipo_horario'] = reserva_tipo_horario
    turno = None

    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA.value
    if reserva_turno is not None:
        turno = db.session.get(Turnos, reserva_turno)
    if not reserva_dia:
        reserva_dia = hoje.date()
    reservas_fixas, reservas_temporarias = get_reservas_por_dia(reserva_dia, turno, TipoAulaEnum(reserva_tipo_horario))
    reservas = []
    i, j = 0, 0
    control_1 = len(reservas_fixas) if reservas_fixas else 0
    control_2 = len(reservas_temporarias) if reservas_temporarias else 0
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
    icons = [
        ["glyphicon-question-sign", "default", "não definido"],
        ["glyphicon-thumbs-down", "danger", "não pegou a chave"],
        ["glyphicon-thumbs-up", "success", "pegou a chave"],
        ["glyphicon-ok", "info", "devolveu a chave"]
    ]
    extras['icons'] = icons
    return render_template("status_reserva/status_reserva.html", username=username, perm=perm, **extras)