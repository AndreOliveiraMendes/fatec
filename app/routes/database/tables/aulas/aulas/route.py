
from flask import Blueprint, abort, g, render_template, request

from app.decorators.decorators import admin_required, crud_route
from app.enums import ActionEnum, StepEnum
from .states import VALID_STATES
from .handlers import dispatcher

bp = Blueprint('database_aulas', __name__, url_prefix="/database")

@bp.route("/aulas", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_aulas():
    if request.method == 'POST':
        try:
            state = (ActionEnum(g.acao), StepEnum(g.bloco))
        except ValueError as e:
            abort(400, "Estado invalido")

        if state not in VALID_STATES:
            abort(400)

        handler = dispatcher.get(state)

        if handler:
            handler()
        
    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/aulas.html", user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)