from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.usuarios import get_pessoas, get_usuarios
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.usuarios import Usuarios
from app.routes_helper.db_actions import db_action
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

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['pessoas'] = get_pessoas()

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
            g.acao, g.extras, pessoas=get_pessoas())

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['pessoas'] = get_pessoas()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_usuario = none_if_empty(request.form.get('id_usuario', None), int)
    id_pessoa = none_if_empty(request.form.get('id_pessoa', None), int)
    tipo_pessoa = none_if_empty(request.form.get('tipo_pessoa', None))
    situacao_pessoa = none_if_empty(request.form.get('situacao_pessoa', None))
    grupo_pessoa = none_if_empty(request.form.get('grupo_pessoa', None))

    novo_usuario = Usuarios(
        id_usuario=id_usuario,
        id_pessoa=id_pessoa,
        tipo_pessoa=tipo_pessoa,
        situacao_pessoa=situacao_pessoa,
        grupo_pessoa=grupo_pessoa
    )

    db_action(
        "Inserção",
        "Usuario cadastrado com sucesso",
        "Erro ao cadastrar usuario",
        obj=novo_usuario
    )

    g.redirect_action, g.bloco = register_return(
        g.url,
        g.acao,
        g.extras,
        pessoas=get_pessoas()
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_usuarios():
    g.extras['usuarios'] = get_usuarios(g.acao, g.userid)

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_usuario():
    id_usuario = none_if_empty(request.form.get('id_usuario', None))
    g.user = db.get_or_404(Usuarios, id_usuario)
    g.extras['usuario'] = g.user
    g.extras['pessoas'] = get_pessoas()

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_usuario = none_if_empty(request.form.get('id_usuario', None), int)

    id_pessoa = get_value_or_abort(
        request.form.get('id_pessoa', None),
        400,
        "O campo 'id_pessoa' é obrigatório.",
        int
    )

    tipo_pessoa = get_value_or_abort(
        request.form.get('tipo_pessoa', None),
        400,
        "O campo 'tipo_pessoa' é obrigatório."
    )

    situacao_pessoa = get_value_or_abort(
        request.form.get('situacao_pessoa', None),
        400,
        "O campo 'situacao_pessoa' é obrigatório."
    )

    grupo_pessoa = none_if_empty(request.form.get('grupo_pessoa', None))

    usuario = db.get_or_404(Usuarios, id_usuario)
    dados_anteriores = copy(usuario)

    def update():
        usuario.id_pessoa = id_pessoa
        usuario.tipo_pessoa = tipo_pessoa
        usuario.situacao_pessoa = situacao_pessoa
        usuario.grupo_pessoa = grupo_pessoa

    db_action(
        "Edição",
        "Usuario atualizado com sucesso",
        "Erro ao editar usuario",
        obj=usuario,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url,
        g.acao,
        g.extras,
        usuarios=get_usuarios(g.acao, g.userid)
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_fetch():
    id_usuario = none_if_empty(request.form.get('id_usuario', None), int)

    usuario = db.get_or_404(Usuarios, id_usuario)

    if g.userid == id_usuario:
        flash("Voce não pode se excluir", "danger")

    else:

        db_action(
            "Exclusão",
            "Usuario excluído com sucesso",
            "Erro ao excluir usuario",
            obj=usuario
        )

    g.redirect_action, g.bloco = register_return(
        g.url,
        g.acao,
        g.extras,
        usuarios=get_usuarios(g.acao, g.userid)
    )