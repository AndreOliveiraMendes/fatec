from flask import Blueprint, render_template, session

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required

bp = Blueprint('gestao_reserva_equipamento', __name__, url_prefix='/gestao_reservas/equipamento')

@bp.route('/')
@admin_required
def gerenciar_reservas_equipamentos():
    userid = session.get('userid')
    user = get_user(userid)
    return render_template("gestão_reservas/reservas_equipamentos/gerenciar.html", user=user)