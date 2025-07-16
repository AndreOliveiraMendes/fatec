import copy
from flask import Blueprint
from flask import flash, session, render_template, request, abort
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import and_, or_
from config.general import PER_PAGE
from app.models import db, Historicos, Usuarios
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_datetime_string, get_user_info, \
    get_query_params, registrar_log_generico_usuario, disable_action, include_action, get_session_or_request, \
    register_return

bp = Blueprint('historicos', __name__, url_prefix="/database")

def get_usuarios():
    return Usuarios.query.all()

def get_tabelas():
    return db.session.query(Historicos.tabela).distinct().all()

def get_categorias():
    return db.session.query(Historicos.categoria).distinct().all()

def get_origens():
    return db.session.query(Historicos.origem).distinct().all()

def filtro_intervalo(inicio_procura, fim_procura):
    if inicio_procura and fim_procura:
        return inicio_procura <= Historicos.data_hora <= fim_procura
    elif inicio_procura:
        return inicio_procura <= Historicos.data_hora
    elif fim_procura:
        return fim_procura >= Historicos.data_hora
    else:
        raise ValueError("Especifique ao menos um valor")
    
def get_conteudo(conteudo):
    return or_(
        Historicos.message.ilike(f"%{conteudo}%"),
        Historicos.chave_primaria.ilike(f"%{conteudo}%"),
        Historicos.observacao.ilike(f"%{conteudo}%")
    )

def get_data():
    id_historico = none_if_empty(request.form.get('id_historico'), int)
    id_usuario = none_if_empty(request.form.get('id_usuario'), int)
    tabela = none_if_empty(request.form.get('tabela'))
    categoria = none_if_empty(request.form.get('categoria'))
    inicio_procura = parse_datetime_string(request.form.get('inicio_procura'))
    fim_procura = parse_datetime_string(request.form.get('fim_procura'))
    origem = none_if_empty(request.form.get('origem'))
    conteudo = none_if_empty(request.form.get('conteudo'))
    filter = []
    query = Historicos.query
    query_params = get_query_params(request)
    if id_historico is not None:
        filter.append(Historicos.id_historico == id_historico)
    if id_usuario is not None:
        filter.append(Historicos.id_usuario == id_usuario)
    if tabela:
        filter.append(Historicos.tabela == tabela)
    if categoria:
        filter.append(Historicos.categoria == categoria)
    if inicio_procura or fim_procura:
        filter.append(filtro_intervalo(inicio_procura, fim_procura))
    if origem:
        filter.append(Historicos.origem == origem)
    if conteudo:
        filter.append(get_conteudo(conteudo))
    return filter, query, query_params

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
            extras['origens'] = get_origens()
        elif acao == 'procurar' and bloco == 1:
            data_filter, query, query_params = get_data()
            if data_filter:
                historicos_paginados = query.filter(*data_filter).paginate(page=page, per_page=PER_PAGE, error_out=False)
                extras['historicos'] = historicos_paginados.items
                extras['pagination'] = historicos_paginados
                extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo:", "danger")
                redirect_action, bloco = register_return('historicos.gerenciar_Historicos', acao, extras,
                    usuarios=get_usuarios(), tabelas=get_tabelas(), categorias=get_categorias(),
                    origens=get_origens()
                )
    if redirect_action:
        return redirect_action
    return render_template("database/historicos.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)