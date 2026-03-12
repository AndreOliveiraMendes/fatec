from flask import Blueprint, g, render_template, request

from app.decorators.decorators import admin_required, crud_route
from app.enums import TipoMovimentacaoEnum
from app.routes_helper.controller import get_controller
from app.routes_helper.ui import disable_action

from .handlers import dispatcher
from .states import VALID_STATES

bp = Blueprint('database_movimentacoes_equipamento', __name__, url_prefix="/database")

@bp.route("/movimentacoes_equipamento", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_movimentacoes_equipamento():
    g.extras['TME'] = TipoMovimentacaoEnum
    disabled = ['inserir', 'editar', 'excluir']
    disable_action(g.extras, disabled)
    if request.method == 'POST':
        get_controller(VALID_STATES, dispatcher, g.acao, g.bloco)

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/movimentacoes_equipamento.html", user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)