import copy
from flask import Blueprint
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Reservas_Fixas
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, \
    get_query_params, registrar_log_generico_usuario, get_session_or_request, register_return


bp = Blueprint('reservas_fixas', __name__, url_prefix="/database")

@bp.route("/reservas_fixa")
@admin_required
def gerenciar_reservas_fixas():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        pass
    if redirect_action:
        return redirect_action
    return render_template("database/reservas_fixas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)