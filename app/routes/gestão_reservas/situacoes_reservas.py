from datetime import datetime
from typing import Any

from flask import Blueprint, abort, render_template, request, session

from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import get_turno_by_time, get_turnos
from app.dao.internal.reservas import get_reservas_por_dia
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.enums import SituacaoChaveEnum, TipoAulaEnum
from app.extensions import db
from app.models.aulas import Turnos

from .handler import process_reservas

bp = Blueprint('situacao_reservas', __name__, url_prefix="/situacoes_reservas")

def verificar_merge_reserva(reserva_1, reserva_2, tolerancia=20):
    mesma_sala = reserva_1.get('local') == reserva_2.get('local')
    mesmo_professor = reserva_1.get('id_responsavel') == reserva_2.get('id_responsavel')

    if not (mesma_sala and mesmo_professor):
        return False

    # pega fim da primeira e início da segunda
    h1 = reserva_1.get('horarios')[-1].aula.horario_fim
    h2 = reserva_2.get('horarios')[0].aula.horario_inicio

    dt1 = datetime.combine(datetime.today(), h1)
    dt2 = datetime.combine(datetime.today(), h2)

    diff_min = abs((dt2 - dt1).total_seconds() // 60)  # sempre positivo

    return diff_min <= tolerancia

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
    extras['reservas'] = process_reservas(reservas_fixas, reservas_temporarias, reserva_dia)
    return render_template("gestão_reservas/situacoes_reservas.html", user=user, **extras)
