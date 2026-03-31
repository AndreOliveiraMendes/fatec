from datetime import date

from flask import Blueprint, render_template, request, session

from app.dao.internal.aulas import get_aulas_ativas_por_dia
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.usuarios import get_pessoas, get_user
from app.decorators.decorators import reserva_equipamento_required
from app.enums import TipoAulaEnum

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
    pessoas = get_pessoas()

    return render_template(
        'reserva_equipamento/main_page.html',
        user=user,
        hoje=today,
        horarios=aulas,
        equipamentos=equipamentos,
        pessoas=pessoas
    )
