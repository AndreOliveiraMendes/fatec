
from flask import Blueprint, g, render_template, request

from app.decorators.decorators import admin_required, crud_route
from app.routes_helper.controller import get_controler

from .handlers import dispatcher
from .states import VALID_STATES

bp = Blueprint('database_semestres', __name__, url_prefix="/database")

@bp.route("/semestres", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_semestres():
    if request.method == 'POST':
        get_controler(VALID_STATES, dispatcher, g.acao, g.bloco)

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/semestres.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)