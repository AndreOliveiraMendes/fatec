import copy

from flask import Blueprint, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_categorias, get_equipamentos
from app.decorators.decorators import admin_required, crud_route
from app.extensions import db
from app.models.equipamentos import Equipamentos
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

bp = Blueprint('database_equipamentos', __name__, url_prefix="/database")

@bp.route("/equipamentos", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_equipamentos():
    if request.method == "POST":
        if g.acao == "listar":
            sel_equipamentos = select(Equipamentos)
            equipamentos_paginados = SelectPagination(
                select=sel_equipamentos, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras["equipamentos"] = equipamentos_paginados.items
            g.extras["pagination"] = equipamentos_paginados

        elif g.acao == "procurar" and g.bloco == 0:
            g.extras["categorias"] = get_categorias()
        elif g.acao == "procurar" and g.bloco == 1:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
            nome_equipamento = none_if_empty(request.form.get('nome_equipamento'))
            descricao = none_if_empty(request.form.get('descricao'))
            id_categoria = none_if_empty(request.form.get('id_categoria'), int)
            filters = []
            query_params = get_query_params(request)
            if id_equipamento is not None:
                filters.append(Equipamentos.id_equipamento == id_equipamento)
            if nome_equipamento:
                filters.append(Equipamentos.nome_equipamento.ilike(f"%{nome_equipamento}%"))
            if descricao:
                filters.append(Equipamentos.descricao.ilike(f"%{descricao}%"))
            if id_categoria is not None:
                filters.append(Equipamentos.id_categoria == id_categoria)
            if filters:
                sel_equipamentos = select(Equipamentos).where(
                    *filters
                )
                equipamentos_paginados = SelectPagination(
                    select=sel_equipamentos, session=db.session,
                    page=g.page, per_page=PER_PAGE, error_out=False
                )
                g.extras['equipamentos'] = equipamentos_paginados.items
                g.extras['pagination'] = equipamentos_paginados
                g.extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                g.redirect_action, g.bloco = register_return(
                    g.url, g.acao, g.extras, categorias=get_categorias()
                )

        elif g.acao == "inserir" and g.bloco == 0:
            g.extras["categorias"] = get_categorias()

        elif g.acao == "inserir" and g.bloco == 1:
            nome_equipamento = none_if_empty(request.form.get('nome_equipamento'))
            descricao = none_if_empty(request.form.get('descricao'))
            id_categoria = none_if_empty(request.form.get('id_categoria'), int)

            novo_equipamento = Equipamentos(
                nome_equipamento=nome_equipamento,
                descricao=descricao,
                id_categoria=id_categoria
            )

            def insert():
                db.session.add(novo_equipamento)

            db_action(
                "Inserção",
                "Equipamento cadastrado com sucesso",
                "Erro ao cadastrar equipamento",
                obj=novo_equipamento,
                action=insert
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                categorias=get_categorias()
            )

        elif g.acao in ['editar', 'excluir'] and g.bloco == 0:
            g.extras["equipamentos"] = get_equipamentos()
        elif g.acao in ['editar', 'excluir'] and g.bloco == 1:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
            equipamento = db.get_or_404(Equipamentos, id_equipamento)
            g.extras['equipamento'] = equipamento
            g.extras['categorias'] = get_categorias()

        elif g.acao == 'editar' and g.bloco == 2:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
            nome_equipamento = get_value_or_abort(request.form.get('nome_equipamento'), 400, "nome da categoria é obrigatorio")
            descricao = none_if_empty(request.form.get('descricao'))
            id_categoria = get_value_or_abort(request.form.get('id_categoria'), 400, "id da categoria é obrigatorio", int)

            equipamento = db.get_or_404(Equipamentos, id_equipamento)
            dados_anteriores = copy.copy(equipamento)

            def update():
                equipamento.nome_equipamento = nome_equipamento
                equipamento.descricao = descricao
                equipamento.id_categoria = id_categoria

            db_action(
                "Edição",
                "Equipamento editado com sucesso",
                "Erro ao editar equipamento",
                obj=equipamento,
                old_obj=dados_anteriores,
                action=update
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                equipamentos=get_equipamentos()
            )

        elif g.acao == 'excluir' and g.bloco == 2:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)

            equipamento = db.get_or_404(Equipamentos, id_equipamento)

            def delete():
                db.session.delete(equipamento)

            db_action(
                "Exclusão",
                "Equipamento deletado com sucesso",
                "Erro ao deletar equipamento",
                obj=equipamento,
                action=delete
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                equipamentos=get_equipamentos()
            )

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/equipamentos.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)