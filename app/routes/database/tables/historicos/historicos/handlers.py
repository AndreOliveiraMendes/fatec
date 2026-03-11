from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import between, func, or_, select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_datetime_string
from app.dao.internal.usuarios import get_usuarios
from app.decorators.decorators import register_handler
from app.enums import OrigemEnum
from app.extensions import db
from app.models.historicos import Historicos
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

def get_tabelas():
    sel_tabelas = select(Historicos.tabela).distinct()
    return db.session.execute(sel_tabelas).all()

def get_categorias():
    sel_categorias = select(Historicos.categoria).distinct()
    return db.session.execute(sel_categorias).all()

def get_origens():
    sel_origens = select(Historicos.origem).distinct()
    return db.session.execute(sel_origens).all()

def filtro_intervalo(inicio_procura, fim_procura):
    if inicio_procura and fim_procura:
        return between(Historicos.data_hora, inicio_procura, fim_procura)
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
    filters = []
    query_params = get_query_params(request)
    if id_historico is not None:
        filters.append(Historicos.id_historico == id_historico)
    if id_usuario is not None:
        filters.append(Historicos.id_usuario == id_usuario)
    if tabela:
        filters.append(Historicos.tabela == tabela)
    if categoria:
        filters.append(Historicos.categoria == categoria)
    if inicio_procura or fim_procura:
        filters.append(filtro_intervalo(inicio_procura, fim_procura))
    if origem:
        filters.append(Historicos.origem == OrigemEnum(origem))
    if conteudo:
        filters.append(get_conteudo(conteudo))
    sel_historicos = select(Historicos)
    return filters, sel_historicos, query_params

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_historicos = select(Historicos)
    historicos_paginados = SelectPagination(
        select=sel_historicos, session=db.session, page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['historicos'] = historicos_paginados.items
    g.extras['pagination'] = historicos_paginados

@register_handler(dispatcher, 'procurar', 0)
@register_handler(dispatcher, 'exportar', 0)
def historicos_prefetch():
    g.extras['usuarios'] = get_usuarios()
    g.extras['tabelas'] = get_tabelas()
    g.extras['categorias'] = get_categorias()
    g.extras['origens'] = get_origens()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    data_filter, sel_historicos, query_params = get_data()
    if data_filter:
        sel_historicos = sel_historicos.where(*data_filter)
        historicos_paginados = SelectPagination(
            select=sel_historicos, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['historicos'] = historicos_paginados.items
        g.extras['pagination'] = historicos_paginados
        g.extras['query_params'] = query_params
    else:
        flash("especifique ao menos um campo:", "danger")
        g.redirect_action, g.bloco = register_return(
            g.url, g.acao, g.extras,
            usuarios=get_usuarios(), tabelas=get_tabelas(), categorias=get_categorias(),
            origens=get_origens()
        )
@register_handler(dispatcher, 'exportar', 1)
def export_fetch():
    data_filter, sel_historicos, query_params = get_data()
    if data_filter:
        sel_historicos = sel_historicos.where(*data_filter)
    sel_count_historicos = (
        select(func.count())
        .select_from(sel_historicos.subquery())
    )
    g.extras['count'] = db.session.execute(sel_count_historicos).scalar()
    g.extras['query_params'] = query_params