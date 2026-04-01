from datetime import date

from flask import Blueprint, render_template, request, session, url_for

from app.dao.internal.reservas import get_reservas_equipamentos
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required

bp = Blueprint('gestao_reserva_equipamento', __name__, url_prefix='/gestao_reservas/equipamento')

@bp.route('/')
@admin_required
def gerenciar_reservas_equipamentos():
    userid = session.get('userid')
    user = get_user(userid)

    reserva_dia = request.args.get('reserva_dia', date.today().isoformat())
    ontem = date.fromisoformat(reserva_dia).fromordinal(date.fromisoformat(reserva_dia).toordinal() - 1)
    amanha = date.fromisoformat(reserva_dia).fromordinal(date.fromisoformat(reserva_dia).toordinal() + 1)

    reservas = get_reservas_equipamentos(reserva_dia)
    for reserva in reservas:
        url = url_for('api_reservas_equipamentos.detalhes_reserva_equipamento', id_reserva = reserva.id_reserva)
        reserva.url_detalhes = url
    return render_template(
        "gestão_reservas/reservas_equipamentos/gerenciar.html",
        user=user,
        reservas=reservas,
        reserva_dia=reserva_dia,
        ontem=ontem.isoformat(),
        amanha=amanha.isoformat()
    )