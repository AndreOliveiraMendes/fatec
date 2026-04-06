from datetime import datetime
from typing import Any

from flask import Blueprint, abort, render_template, session

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import login_required
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

    return render_template("usuario/reservas_auditorios/reservas_auditorios.html", user=user, **extras)