import copy

from flask import Blueprint, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import get_session_or_request, get_user_info
from app.auxiliar.decorators import admin_required

bp = Blueprint('database_reserva_auditorio', __name__, url_prefix="/database")

@bp.route('/reserva_auditorio')
@admin_required
def gerenciar_reserva_auditorio():
    url = 'database_reserva_auditorio.gerenciar_reserva_auditorio'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {'url':url}
    if request.method == 'POST':
        pass
    if redirect_action:
        return redirect_action
    return render_template("database/table/reserva_auditorio.html",
        username=username, perm=perm, acao=acao, bloco=bloco, **extras)