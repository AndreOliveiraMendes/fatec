import copy
from flask import Blueprint
from flask import flash, session, render_template, request, abort
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import select
from config.general import PER_PAGE
from app.models import db, Historicos, Usuarios
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, \
    get_query_params, registrar_log_generico_usuario, disable_action, include_action, get_session_or_request, \
    register_return

bp = Blueprint('historicos', __name__, url_prefix="/database")

def get_usuarios():
    return Usuarios.query.all()

def get_tabelas():
    return db.session.query(Historicos.tabela).distinct().all()

def get_categorias():
    return db.session.query(Historicos.categoria).distinct().all()

@bp.route("/historicos", methods=["GET", "POST"])
@admin_required
def gerenciar_Historicos():
    redirect_action = None
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
    user_agent = request.headers.get('User-Agent')
    is_mobile = 'Mobile' in user_agent
    extras['is_mobile'] = is_mobile
    if request.method == 'POST':
        if acao in disabled:
            abort(403, description="Esta funcionalidade não foi implementada.")
        if acao == 'listar':
            historicos_paginados = Historicos.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['historicos'] = historicos_paginados.items
            extras['pagination'] = historicos_paginados

        if acao == 'procurar' and bloco == 0:
            extras['usuarios'] = get_usuarios()
            extras['tabelas'] = get_tabelas()
            extras['categorias'] = get_categorias()
    return render_template("database/historicos.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)