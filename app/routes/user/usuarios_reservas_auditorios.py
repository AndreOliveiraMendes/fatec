from flask import Blueprint, render_template
from requests import session

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import login_required


bp = Blueprint('usuarios_reservas_auditorios', __name__, url_prefix='/usuario')

@bp.route("/reservas/reservas_auditorios")
@login_required
def gerenciar_reservas_auditorios():
    userid = session.get('userid')
    user = get_user(userid)

    return render_template("")