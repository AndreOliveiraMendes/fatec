from flask import Blueprint, render_template, session
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import get_user_info

bp = Blueprint('situacao_reserva', __name__, url_prefix="/status_reserva")

@bp.route('/')
@admin_required
def gerenciar_status():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("status_reserva/status_reserva.html", username=username, perm=perm)