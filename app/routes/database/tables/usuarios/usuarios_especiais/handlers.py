import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.usuarios import get_usuarios_especiais
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.usuarios import Usuarios_Especiais
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, "listar", 0)
def list_handler():
    sel_users = select(Usuarios_Especiais)
    usuarios_especiais_paginados = SelectPagination(
        select=sel_users, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['usuarios_especiais'] = usuarios_especiais_paginados.items
    g.extras['pagination'] = usuarios_especiais_paginados

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)
    nome_usuario_especial = none_if_empty(request.form.get('nome_usuario_especial'))
    exact_name_match = 'emnome' in request.form
    filters = []
    query_params = get_query_params(request)
    if id_usuario_especial is not None:
        filters.append(Usuarios_Especiais.id_usuario_especial == id_usuario_especial)
    if nome_usuario_especial:
        if exact_name_match:
            filters.append(Usuarios_Especiais.nome_usuario_especial == nome_usuario_especial)
        else:
            filters.append(
                Usuarios_Especiais.nome_usuario_especial.ilike(f"%{nome_usuario_especial}%"))
    if filters:
        sel_users = select(Usuarios_Especiais).where(*filters)
        usuarios_especiais_paginados = SelectPagination(
            select=sel_users, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['usuarios_especiais'] = usuarios_especiais_paginados.items
        g.extras['pagination'] = usuarios_especiais_paginados
        g.extras['query_params'] = query_params
    else:
        flash("especifique pelo menos um campo de busca", "danger")
        g.redirect_action, g.bloco = register_return(
            g.url, g.acao, g.extras)

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    nome_usuario_especial = none_if_empty(request.form.get('nome_usuario_especial'))

    novo_usuario_especial = Usuarios_Especiais(
        nome_usuario_especial=nome_usuario_especial
    )

    def insert():
        db.session.add(novo_usuario_especial)

    db_action(
        "Inserção",
        "Usuario Especial cadastrada com sucesso",
        "Erro ao cadastrar usuario especial",
        obj=novo_usuario_especial,
        action=insert
    )

    g.redirect_action, g.bloco = register_return(
        g.url,
        g.acao,
        g.extras
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_usuarios_especiais():
    g.extras['usuarios_especiais'] = get_usuarios_especiais()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_usuario_especial():
    id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)
    usuario_especial = db.get_or_404(Usuarios_Especiais, id_usuario_especial)
    g.extras['usuario_especial'] = usuario_especial

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)

    nome_usuario_especial = get_value_or_abort(
        request.form.get('nome_usuario_especial'),
        400,
        "nome do usuario especial é obrigatorio"
    )

    usuario_especial = db.get_or_404(Usuarios_Especiais, id_usuario_especial)
    dados_anteriores = copy.copy(usuario_especial)

    def update():
        usuario_especial.nome_usuario_especial = nome_usuario_especial

    db_action(
        "Edição",
        "Usuario especial editado com sucesso",
        "Erro ao editar usuario especial",
        obj=usuario_especial,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url,
        g.acao,
        g.extras,
        usuarios_especiais=get_usuarios_especiais()
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)

    usuario_especial = db.get_or_404(Usuarios_Especiais, id_usuario_especial)

    def delete():
        db.session.delete(usuario_especial)

    db_action(
        "Exclusão",
        "Usuario especial excluido com sucesso",
        "Erro ao excluir usuario especial",
        obj=usuario_especial,
        action=delete
    )

    g.redirect_action, g.bloco = register_return(
        g.url,
        g.acao,
        g.extras,
        usuarios_especiais=get_usuarios_especiais()
    )