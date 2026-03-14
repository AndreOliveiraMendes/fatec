from datetime import datetime
from typing import Any

from flask import Blueprint, abort, request, session

from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import get_turno_by_time, get_turnos
from app.decorators.decorators import admin_required
from app.enums import SituacaoChaveEnum, TipoAulaEnum
from config.json_related import carregar_config_geral

from .handler import (atualizar_situacoes_fixa, atualizar_situacoes_temporaria,
                      gerenciar_situacoes_reservas_fixas,
                      gerenciar_situacoes_reservas_temporarias)

bp = Blueprint('gestao_reserva', __name__, url_prefix="/gestao_reservas")

@bp.route('/<tipo_reserva>')
@admin_required
def gerenciar_situacoes(tipo_reserva):
    if not tipo_reserva in ['fixa', 'temporaria']:
        abort(404, description="Tipo de reserva inválido.")
    icons = [
        ["glyphicon-thumbs-down", "danger", "Não pegou a chave"],
        ["glyphicon-thumbs-up", "success", "Pegou a chave"],
        ["glyphicon-ok", "info", "Reserva concluida"] 
    ]
    hoje = datetime.today()
    extras: dict[str, Any] = {'hoje':hoje}
    extras['icons'] = icons
    extras['situacaoChave'] = list(zip(SituacaoChaveEnum, icons))
    reserva_dia = parse_date_string(request.args.get('reserva-dia', default=hoje.date().strftime("%Y-%m-%d")))
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    if not 'reserva_turno' in request.args:
        reserva_turno = get_turno_by_time(hoje.time())
        if reserva_turno:
            reserva_turno = reserva_turno.id_turno
    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA.value
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    extras['reserva_tipo_horario'] = reserva_tipo_horario
    extras['config'] = carregar_config_geral()
    if tipo_reserva == 'fixa':
        return gerenciar_situacoes_reservas_fixas(extras)
    elif tipo_reserva == 'temporaria':
        return gerenciar_situacoes_reservas_temporarias(extras)
    else:
        abort(404, description="Tipo de reserva inválido.")

@bp.route('/<tipo_reserva>/<int:lab>/<data:dia>', methods=['POST'])
@admin_required
def atualizar_situacoes(tipo_reserva, lab, dia):
    userid = session.get('userid')
    common = {}
    common['userid'] = userid
    common['lab'] = lab
    common['dia'] = dia
    common['tipo_reserva'] = tipo_reserva
    common['aulas'] = request.form.getlist('aulas')
    common['chave'] = request.form.get('situacao')
    if tipo_reserva == 'fixa':
        return atualizar_situacoes_fixa(common)
    elif tipo_reserva == 'temporaria':
        return atualizar_situacoes_temporaria(common)
    else:
        abort(404, description="Tipo de reserva inválido.")
