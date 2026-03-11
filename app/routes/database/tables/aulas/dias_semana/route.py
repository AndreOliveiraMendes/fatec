
from flask import Blueprint, g, render_template, request

from app.decorators.decorators import admin_required, crud_route
from app.routes_helper.controller import get_controler
from app.routes_helper.ui import disable_action

from .handlers import dispatcher
from .states import VALID_STATES

bp = Blueprint('database_dias_da_semana', __name__, url_prefix="/database")

@bp.route("/dias_da_semana", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_dias_da_semana():
    disabled = ['procurar']
    disable_action(g.extras, disabled)
    if request.method == 'POST':
        get_controler(VALID_STATES, dispatcher, g.acao, g.bloco)

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/dias_da_semana.html", user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)