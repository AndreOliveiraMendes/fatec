from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_categorias
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.equipamentos import Categorias_de_Equipamentos
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, "listar", 0)
def list_handler():
    sel_categorias = select(Categorias_de_Equipamentos)
    categorias_paginas = SelectPagination(
        select=sel_categorias, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['categorias'] = categorias_paginas.items
    g.extras['pagination'] = categorias_paginas

@register_handler(dispatcher, "procurar", 1)
def search_fetch():
    id_categoria = none_if_empty(request.form.get('id_categoria'), int)
    nome_categoria = none_if_empty(request.form.get('nome_categoria'))
    descricao = none_if_empty(request.form.get('descricao'))
    filters = []
    query_params = get_query_params(request)
    if id_categoria is not None:
        filters.append(Categorias_de_Equipamentos.id_categoria == id_categoria)
    if nome_categoria:
        filters.append(Categorias_de_Equipamentos.nome_categoria.ilike(f"%{nome_categoria}%"))
    if descricao:
        filters.append(Categorias_de_Equipamentos.descricao.ilike(f"%{descricao}%"))
    if filters:
        sel_categorias = select(Categorias_de_Equipamentos).where(
            *filters
        )
        categorias_paginas = SelectPagination(
            select=sel_categorias, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['categorias'] = categorias_paginas.items
        g.extras['pagination'] = categorias_paginas
        g.extras['query_params'] = query_params
    else:
        flash("especifique pelo menos um campo de busca", "danger")
        g.redirect_action, g.bloco = register_return(
            g.url, g.acao, g.extras
        )

@register_handler(dispatcher, "inserir", 1)
def insert_push():
    nome_categoria = none_if_empty(request.form.get('nome_categoria'))
    codigo = none_if_empty(request.form.get('codigo'))
    descricao = none_if_empty(request.form.get('descricao'))

    nova_categoria = Categorias_de_Equipamentos(
        nome_categoria=nome_categoria,
        codigo = codigo,
        descricao=descricao
    )

    db_action(
        "Inserção",
        "categoria cadastrada com sucesso",
        "erro ao cadastrar categoria",
        obj=nova_categoria
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_categorias():
    g.extras['categorias'] = get_categorias()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_categoria():
    id_categoria = none_if_empty(request.form.get('id_categoria'))
    categoria = db.get_or_404(Categorias_de_Equipamentos, id_categoria)
    g.extras['categoria'] = categoria

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_categoria = none_if_empty(request.form.get('id_categoria'), int)
    nome_categoria = get_value_or_abort(request.form.get('nome_categoria'), 400, "nome é obrigatorio")
    codigo = get_value_or_abort(request.form.get('codigo'), 400, "codigo é obrigatorio")
    descricao = none_if_empty(request.form.get('descricao'))

    categoria = db.get_or_404(Categorias_de_Equipamentos, id_categoria)
    dados_anteriores = copy(categoria)

    def update():
        categoria.nome_categoria = nome_categoria
        categoria.codigo = codigo
        categoria.descricao = descricao

    db_action(
        "Edição",
        "Categoria editada com sucesso",
        "Erro ao editar categoria",
        obj=categoria,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        categorias=get_categorias()
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_categoria = none_if_empty(request.form.get('id_categoria'), int)

    categoria = db.get_or_404(Categorias_de_Equipamentos, id_categoria)

    db_action(
        "Exclusão",
        "Categoria excluida com sucesso",
        "Erro ao excluir categoria",
        obj=categoria
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        categorias=get_categorias()
    )