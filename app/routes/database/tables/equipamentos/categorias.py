import copy

from flask import Blueprint, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_categorias
from app.decorators.decorators import admin_required, crud_route
from app.extensions import db
from app.models.equipamentos import Categorias_de_Equipamentos
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

bp = Blueprint('database_categorias_de_equipamentos', __name__, url_prefix="/database")

@bp.route("/categorias_de_equipamentos", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_categorias_de_equipamentos():
    if request.method == 'POST':
        if g.acao == "listar":
            sel_categorias = select(Categorias_de_Equipamentos)
            categorias_paginas = SelectPagination(
                select=sel_categorias, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['categorias'] = categorias_paginas.items
            g.extras['pagination'] = categorias_paginas

        elif g.acao == "procurar" and g.bloco == 1:
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
        
        elif g.acao == "inserir" and g.bloco == 1:
            nome_categoria = none_if_empty(request.form.get('nome_categoria'))
            descricao = none_if_empty(request.form.get('descricao'))

            nova_categoria = Categorias_de_Equipamentos(
                nome_categoria=nome_categoria,
                descricao=descricao
            )

            def insert():
                db.session.add(nova_categoria)

            db_action(
                "Inserção",
                "categoria cadastrada com sucesso",
                "erro ao cadastrar categoria",
                obj=nova_categoria,
                action=insert
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras
            )

        elif g.acao in ['editar', 'excluir'] and g.bloco == 0:
            g.extras['categorias'] = get_categorias()
        elif g.acao in ['editar', 'excluir'] and g.bloco == 1:
            id_categoria = none_if_empty(request.form.get('id_categoria'))
            categoria = db.get_or_404(Categorias_de_Equipamentos, id_categoria)
            g.extras['categoria'] = categoria

        elif g.acao == 'editar' and g.bloco == 2:
            id_categoria = none_if_empty(request.form.get('id_categoria'), int)
            nome_categoria = get_value_or_abort(request.form.get('nome_categoria'), 400, "nome é obrigatorio")
            descricao = none_if_empty(request.form.get('descricao'))

            categoria = db.get_or_404(Categorias_de_Equipamentos, id_categoria)
            dados_anteriores = copy.copy(categoria)

            def update():
                categoria.nome_categoria = nome_categoria
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

        elif g.acao == 'excluir' and g.bloco == 2:
            id_categoria = none_if_empty(request.form.get('id_categoria'), int)

            categoria = db.get_or_404(Categorias_de_Equipamentos, id_categoria)

            def delete():
                db.session.delete(categoria)

            db_action(
                "Exclusão",
                "Categoria excluida com sucesso",
                "Erro ao excluir categoria",
                obj=categoria,
                action=delete
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                categorias=get_categorias()
            )

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/categorias_de_equipamento.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)