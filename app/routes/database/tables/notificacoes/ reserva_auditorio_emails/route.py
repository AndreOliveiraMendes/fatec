from flask import Blueprint, g, render_template, request

from app.decorators.decorators import admin_required, crud_route
from app.enums import StatusEmailEnum
from app.routes_helper.controller import get_controller

from .handlers import dispatcher
from .states import VALID_STATES

bp = Blueprint('database_reserva_auditorio_emails', __name__, url_prefix="/database")

@bp.route("/reserva_auditorio_emails", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_reserva_auditorio_emails():
    g.extras['SEE'] = StatusEmailEnum
    if request.method == 'POST':
        get_controller(VALID_STATES, dispatcher, g.acao, g.bloco)

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/reserva_auditorio_emails.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)