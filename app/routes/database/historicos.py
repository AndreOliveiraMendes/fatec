import copy
from flask import Blueprint
from flask import flash, session, render_template, request, abort
from sqlalchemy.exc import IntegrityError
from config import PER_PAGE, AFTER_ACTION
from app.models import db, Historicos
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, get_query_params, registrar_log_generico, disable_action, include_action, get_session_or_request

bp = Blueprint('historicos', __name__, url_prefix="/database")

@bp.route("/historicos", methods=["GET", "POST"])
@admin_required
def gerenciar_Historicos():
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    disabled = ['inserir', 'editar', 'excluir']
    include = [{'label':"Exportar", 'value':"exportar", 'icon':"glyphicon-download"}]
    extras = {}
    disable_action(extras, disabled)
    include_action(extras, include)
    if request.method == 'POST':
        if acao in disabled:
            abort(403, description="Esta funcionalidade está desabilitada no momento.")
        if acao == 'listar':
            historicos_paginados = Historicos.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['historicos'] = historicos_paginados.items
            extras['pagination'] = historicos_paginados
    return render_template("database/historicos.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)