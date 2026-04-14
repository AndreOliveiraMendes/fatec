from datetime import datetime
from typing import Any

from flask import Blueprint, abort, render_template, request, session

from app.dao.internal.aulas import get_dias_da_semana
from app.dao.internal.locais import get_auditorios
from app.dao.internal.usuarios import get_pessoas, get_user
from app.decorators.decorators import login_required
from app.enums import StatusReservaAuditorioEnum
from app.routes.user.handler.handler_auditorios import get_reservas_auditorios
from app.routes_helper.request import get_query_params
from config.general import LOCAL_TIMEZONE

bp = Blueprint('usuarios_reservas_auditorios', __name__, url_prefix='/usuario')

@bp.route("/reservas/reservas_auditorios")
@login_required
def gerenciar_reservas_auditorios():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    today = datetime.now(LOCAL_TIMEZONE)
    extras: dict[str, Any] = {'datetime':today}
    args_extras = get_query_params(request, origin="args")
    page = int(request.args.get("page", 1))
    reservas_auditorio = get_reservas_auditorios(userid, args_extras, page)
    extras['reservas_auditorios'] = reservas_auditorio.items
    for reserva in extras['reservas_auditorios']:
        reserva.dentro_periodo = reserva.dia_reserva >= today.date()
    extras['pagination'] = reservas_auditorio
    extras['args_extras'] = args_extras

    # for edit and filter
    extras['pessoas'] = get_pessoas()
    extras['auditorios'] = get_auditorios()
    extras['semanas'] = get_dias_da_semana()
    extras['status'] = StatusReservaAuditorioEnum
    return render_template("usuario/reservas_auditorios/reservas_auditorios.html", user=user, **extras)