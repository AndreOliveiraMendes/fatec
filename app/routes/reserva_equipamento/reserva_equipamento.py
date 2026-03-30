from datetime import date

from flask import Blueprint, jsonify, render_template, request, session

from app.dao.internal.aulas import get_aulas_ativas_por_dia
from app.dao.internal.controle import get_equipamento_disponibilidade_dia
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.reservas import get_quantidade_equipamentos_reservados
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import reserva_equipamento_required
from app.enums import StatusReservaEquipamentoEnum, TipoAulaEnum

bp = Blueprint('reserva_equipamento', __name__, url_prefix='/reserva_equipamento')

@bp.route('/')
@reserva_equipamento_required
def main_page():
    user = get_user(session.get('userid'))

    today_str = request.args.get('dia')
    
    if today_str:
        today = date.fromisoformat(today_str)
    else:
        today = date.today()

    aulas = get_aulas_ativas_por_dia(today, tipo_aula=TipoAulaEnum.AULA)
    equipamentos = get_equipamentos()

    return render_template(
        'reserva_equipamento/main_page.html',
        user=user,
        hoje=today,
        horarios=aulas,
        equipamentos=equipamentos
    )

@bp.route('/resumo')
@reserva_equipamento_required
def get_resumo():
    data = request.args.get("data")

    total = get_equipamento_disponibilidade_dia(data)
    reservado = get_quantidade_equipamentos_reservados(data)
    planejado = get_quantidade_equipamentos_reservados(
        data,
        stats=[StatusReservaEquipamentoEnum.PENDENTE]
    )

    # pega todos os ids possíveis
    ids = set(total) | set(reservado) | set(planejado)

    resumo = {}

    for eq_id in ids:
        t = total.get(eq_id, 0)
        r = reservado.get(eq_id, 0)
        p = planejado.get(eq_id, 0)

        resumo[eq_id] = {
            "total": t,
            "reservado": r,
            "pendente": p,
            "disponivel": t - r,
            "disponivel_planejado": t - r - p
        }

    return jsonify(resumo)