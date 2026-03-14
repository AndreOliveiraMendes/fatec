from datetime import datetime
from typing import Any

from flask import Blueprint, abort, render_template, request, session

from app.auxiliar.parsing import parse_date_string
from app.auxiliar.shared import resolver_reserva
from app.dao.internal.aulas import get_turno_by_time, get_turnos
from app.dao.internal.reservas import get_reservas_por_dia
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.enums import SituacaoChaveEnum, TipoAulaEnum
from app.extensions import db
from app.models.aulas import Turnos
from config.json_related import carregar_config_geral

from .handler import process_reservas

bp = Blueprint('situacao_reservas', __name__, url_prefix="/situacoes_reservas")



@bp.route('/')
@admin_required
def gerenciar_situacoes():
    userid = session.get('userid')
    user = get_user(userid)
    
    hoje = datetime.today()
    extras: dict[str, Any] = {'hoje':hoje}
    icons = [
        ["glyphicon-thumbs-down", "danger", "Não pegou a chave"],
        ["glyphicon-thumbs-up", "success", "Pegou a chave"],
        ["glyphicon-ok", "info", "Reserva concluida"] 
    ]
    extras['icons'] = icons
    extras['situacaoChave'] = list(zip(SituacaoChaveEnum, icons))
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    reserva_dia = parse_date_string(request.args.get('reserva-dia'))
    if not reserva_dia:
        reserva_dia = hoje.date()
    extras['reserva_dia'] = reserva_dia
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    if not 'reserva_turno' in request.args:
        reserva_turno = get_turno_by_time(hoje.time())
        if not reserva_turno is None:
            reserva_turno = reserva_turno.id_turno
    if reserva_turno is not None:
        reserva_turno = db.get_or_404(Turnos, reserva_turno)
    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA
    else:
        try:
            reserva_tipo_horario = TipoAulaEnum(reserva_tipo_horario)
        except ValueError:
            abort(400, "erro ao processar o tipo de horario")
    reservas_fixas, reservas_temporarias = get_reservas_por_dia(reserva_dia, reserva_turno, reserva_tipo_horario)
    extras['config'] = carregar_config_geral()
    pre_processed_reservas = process_reservas(reservas_fixas, reservas_temporarias, reserva_dia)
    reservas = []
    for r in pre_processed_reservas:
        fixa, temp, exibicao = r.fixa, r.temporaria, r.exibicao
        choose, tipo = resolver_reserva(temp, fixa, exibicao)
    return render_template("gestão_reservas/situacoes_reservas.html", user=user, **extras)
