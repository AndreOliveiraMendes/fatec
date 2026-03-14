
from flask import Blueprint, render_template, session

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required

bp = Blueprint('comandos_remotos', __name__, url_prefix="/situacoes_reservas")

@bp.route('/comandos_remotos')
@admin_required
def comandos_remotos():
    userid = session.get('userid')
    user = get_user(userid)
    return render_template("gestão_reservas/remote_commands.html", user=user)