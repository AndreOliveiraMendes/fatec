from flask import Blueprint, render_template, session, request
from datetime import datetime
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string
from app.auxiliar.dao import get_reservas_por_dia, get_turnos

bp = Blueprint('situacao_reserva', __name__, url_prefix="/status_reserva")

@bp.route('/')
@admin_required
def gerenciar_status():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    hoje = datetime.today()
    extras = {'hoje':hoje}
    reserva_dia = parse_date_string(request.args.get('reserva-dia', default=hoje.date().strftime("%Y-%m-%d")))
    reserva_turno = request.args.get('reserva_turno', type=int)
    extras['turnos'] = get_turnos()
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    return render_template("status_reserva/status_reserva.html", username=username, perm=perm, **extras)