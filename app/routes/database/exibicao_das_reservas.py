import copy

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (disable_action,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.decorators import admin_required
from app.models import Exibicao_Reservas, FinalidadeTipoReservaEnum, db
from config.general import PER_PAGE

bp = Blueprint('database_exibicao_reservas', __name__, url_prefix="/database")

@bp.route("/exibicao_reservas", methods=["GET", "POST"])
@admin_required
def gerenciar_exibicao_reservas():
    url = 'database_exibicao_reservas.gerenciar_exibicao_reservas'
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
    return render_template("database/table/exibicao_reservas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)