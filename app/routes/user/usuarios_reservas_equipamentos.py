from datetime import datetime
from typing import Any

from flask import Blueprint, abort, render_template, request, session

from app.dao.internal.aulas import get_dias_da_semana
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.usuarios import get_pessoas, get_user
from app.decorators.decorators import login_required
from app.enums import StatusReservaEquipamentoEnum
from app.routes.user.handler.handler_equipamentos import get_reservas_equipamentos
from app.routes_helper.request import get_query_params
from config.general import LOCAL_TIMEZONE


bp = Blueprint('usuarios_reservas_equipamentos', __name__, url_prefix='/usuario')

@bp.route("/reservas/reservas_equipamentos")
@login_required
def gerenciar_reservas_equipamentos():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    today = datetime.now(LOCAL_TIMEZONE)
    extras: dict[str, Any] = {'datetime':today}
    args_extras = get_query_params(request, origin="args")
    page = int(request.args.get("page", 1))
    reservas_equipamentos = get_reservas_equipamentos(userid, args_extras, page)
    extras['reservas_equipamentos'] = reservas_equipamentos.items
    extras['pagination'] = reservas_equipamentos
    extras['args_extras'] = args_extras

    # for edit and filter
    extras['pessoas'] = get_pessoas()
    extras['pessoasList'] = [{"value":p.id_pessoa, "label": p.nome_pessoa} for p in extras['pessoas']]
    extras['equipamentos'] = get_equipamentos()
    extras['semanas'] = get_dias_da_semana()
    extras['status'] = StatusReservaEquipamentoEnum
    return render_template("usuario/reservas_equipamentos/reservas_equipamentos.html", user=user, **extras)