import random
from datetime import datetime
from typing import Any

from flask import (Blueprint, current_app, redirect, render_template, request,
                   session, url_for)

from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import (get_aulas_ativas_por_dia,
                                    get_turno_by_time, get_turnos)
from app.dao.internal.locais import get_laboratorios
from app.dao.internal.usuarios import get_user
from app.enums import TipoAulaEnum
from app.extensions import db
from app.models.aulas import Turnos
from config.general import LOCAL_TIMEZONE
from config.json_related import carregar_config_geral, carregar_painel_config

bp = Blueprint('consultar_reservas', __name__, url_prefix="/consultar_reserva")

def divide(l, q):
    result = []
    qt = len(l)
    start = 0
    extra = qt%q
    merge = extra <= qt
    qtq = qt//q
    for g in range(qtq):
        end = start + q + (1 if merge and g < extra else 0)
        end = min(end, qt)
        result.append(l[start:end])
        start += end - start
    else:
        if start < qt:
            result.append(l[start:])
    return result

@bp.route('/')
def main_page():
    userid = session.get('userid')
    user = get_user(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras: dict[str, Any] = {'dia':today}
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
    locais = get_laboratorios(True)
    if len(aulas) == 0 or len(locais) == 0:
        extras['skip'] = True
    extras['aulas'] = aulas
    extras['locais'] = locais
    return render_template("reserva/main.html", user=user, **extras)

@bp.route("/televisor")
def tela_televisor():
    telas = [
        url_for('consultar_reservas.tela_televisor1'),
        url_for('consultar_reservas.tela_televisor2'),
        url_for('consultar_reservas.tela_televisor3')
    ]

    cfg = carregar_config_geral()
    tela = cfg.get('tela_padrao')

    if tela and str(tela) in {"1", "2", "3"}:
        return redirect(telas[int(tela) - 1])
    else:
        current_app.logger.warning(
            "tela não configurada ou inválida, usando aleatória"
        )
        return redirect(random.choice(telas))

@bp.route("/televisor1")
def tela_televisor1():
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {}
    painel_cfg = carregar_painel_config().get('estilo1', {})
    tipo_horario = painel_cfg.get('tipo', TipoAulaEnum.AULA.value)
    intervalo = int(painel_cfg.get('tempo', 15))
    qt_lab = int(painel_cfg.get('laboratorios', 6))
    locais = divide(get_laboratorios(True), qt_lab)
    today = datetime.now(LOCAL_TIMEZONE)
    turno = get_turno_by_time(today.time())
    aulas = get_aulas_ativas_por_dia(today.date(), turno, TipoAulaEnum(tipo_horario))
    extras['intervalo'] = intervalo*1000
    extras['locais'] = locais
    extras['hoje'] = today
    extras['aulas'] = aulas
    return render_template("reserva/televisor.html", user=user, **extras)

@bp.route("/televisor2")
def tela_televisor2():
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {}
    painel_cfg = carregar_painel_config().get('estilo2', {})
    tipo_horario = painel_cfg.get('tipo', TipoAulaEnum.AULA.value)
    intervalo = int(painel_cfg.get('tempo', 5))
    qt_lab = int(painel_cfg.get('laboratorios', 6))
    locais = divide(get_laboratorios(True), qt_lab)
    today = datetime.now(LOCAL_TIMEZONE)
    turno = get_turno_by_time(today.time())
    aulas = get_aulas_ativas_por_dia(today.date(), turno, TipoAulaEnum(tipo_horario))
    extras['intervalo'] = intervalo*1000
    extras['locais'] = locais
    extras['hoje'] = today
    extras['aulas'] = aulas
    return render_template("reserva/televisor2.html", user=user, **extras)

@bp.route("/televisor3")
def tela_televisor3():
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {}
    painel_cfg = carregar_painel_config().get('estilo3', {})
    tipo_horario = painel_cfg.get('tipo', TipoAulaEnum.AULA.value)
    intervalo = int(painel_cfg.get('tempo', 5))
    locais = get_laboratorios(True)
    today = datetime.now(LOCAL_TIMEZONE)
    turno = get_turno_by_time(today.time())
    aulas = get_aulas_ativas_por_dia(today.date(), turno, TipoAulaEnum(tipo_horario))
    extras['intervalo'] = intervalo*1000
    extras['locais'] = locais
    extras['hoje'] = today
    extras['aulas'] = aulas
    return render_template("reserva/televisor3.html", user=user, **extras)