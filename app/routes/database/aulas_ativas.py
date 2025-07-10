import copy
from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from sqlalchemy.exc import IntegrityError
from config import PER_PAGE
from app.models import db, Aulas_Ativas
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, \
    get_query_params, registrar_log_generico, get_session_or_request, register_return

bp = Blueprint('aulas_ativas', __name__, url_prefix="/database")

@bp.route("/aulas_ativas", methods=["GET", "POST"])
@admin_required
def gerenciar_aulas_ativas():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            aulas_ativas_paginadas = Aulas_Ativas.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['aulas_ativas'] = aulas_ativas_paginadas.items
            extras['pagination'] = aulas_ativas_paginadas
    return render_template("database/aulas_ativas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)