from flask import Blueprint, g, render_template, request

from app.decorators.decorators import admin_required, crud_route
from app.enums import StatusReservaEquipamentoEnum
from app.routes_helper.controller import get_controller
from app.routes_helper.ui import disable_action

from .handlers import dispatcher
from .states import VALID_STATES

bp = Blueprint('database_reservas_equipamentos', __name__, url_prefix="/database")

@bp.route('reservas_equipamentos', methods=['GET', 'POST'])
@admin_required
@crud_route()
def gerenciar_reservas_equipamentos():
    g.extras['SREE'] = StatusReservaEquipamentoEnum
    disabled = ['inserir', 'editar', 'excluir']
    disable_action(g.extras, disabled)
    if request.method == 'POST':
        get_controller(VALID_STATES, dispatcher, g.acao, g.bloco)
    
    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/reservas_equipamentos.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)