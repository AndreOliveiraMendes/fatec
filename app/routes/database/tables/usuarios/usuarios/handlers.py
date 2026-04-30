
from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.usuarios import Usuarios
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_users = select(Usuarios)
    usuarios_paginados = SelectPagination(
        select=sel_users, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['usuarios'] = usuarios_paginados.items
    g.extras['pagination'] = usuarios_paginados
    g.extras['userid'] = g.userid

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_usuario = none_if_empty(request.form.get('id_usuario', None), int)
    id_pessoa = none_if_empty(request.form.get('id_pessoa', None), int)
    tipo_pessoa = none_if_empty(request.form.get('tipo_pessoa', None))
    situacao_pessoa = none_if_empty(request.form.get('situacao_pessoa', None))
    grupo_pessoa = none_if_empty(request.form.get('grupo_pessoa', None))
    filters = []
    query_params = get_query_params(request)
    if id_usuario is not None:
        filters.append(Usuarios.id_usuario == id_usuario)
    if id_pessoa is not None:
        filters.append(Usuarios.id_pessoa == id_pessoa)
    if tipo_pessoa:
        filters.append(Usuarios.tipo_pessoa == tipo_pessoa)
    if situacao_pessoa:
        filters.append(Usuarios.situacao_pessoa == situacao_pessoa)
    if grupo_pessoa:
        filters.append(Usuarios.grupo_pessoa == grupo_pessoa)
    if filters:
        sel_users = select(Usuarios).where(*filters)
        usuarios_paginados = SelectPagination(
            select=sel_users, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['usuarios'] = usuarios_paginados.items
        g.extras['pagination'] = usuarios_paginados
        g.extras['userid'] = g.userid
        g.extras['query_params'] = query_params
    else:
        flash("especifique pelo menos um campo de busca", "danger")
        g.redirect_action, g.bloco = register_return(g.url,
            g.acao, g.extras)