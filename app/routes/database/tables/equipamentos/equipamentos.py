from typing import Any

from flask import Blueprint, render_template, request, session

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.routes_helper.request import get_session_or_request


bp = Blueprint('database_equipamentos', __name__, url_prefix="/database")

@bp.route("/equipamentos", methods=["GET", "POST"])
@admin_required
def gerenciar_equipamentos():
    url = 'database_equipamentos.gerenciar_equipamentos'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {'url':url}
    if request.method == "POST":
        pass
    if redirect_action:
        return redirect_action
    return render_template("database/table/equipamentos.html",
        user=user, acao=acao, bloco=bloco, **extras)