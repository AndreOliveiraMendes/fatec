import copy

from flask import Blueprint, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_categorias, get_equipamentos
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.decorators.decorators import admin_required, crud_route
from app.extensions import db
from app.models.equipamentos import Equipamentos
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

            try:
                novo_equipamento = Equipamentos(
                    nome_equipamento = nome_equipamento,
                    descricao = descricao,
                    id_categoria = id_categoria
                )
                db.session.add(novo_equipamento)

                db.session.flush()
                registrar_log_generico_usuario(g.userid, 'Inserção', novo_equipamento)

                db.session.commit()
                flash("Equipamento cadastrado com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao cadastrar equipamento")
            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras, categorias=get_categorias()
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
            try:
                equipamento.nome_equipamento = nome_equipamento
                equipamento.descricao = descricao
                equipamento.id_categoria = id_categoria

                db.session.flush()
                registrar_log_generico_usuario(g.userid, 'Edição', equipamento, dados_anteriores)

                db.session.commit()
                flash("Equipamento editado com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar equipamento")
            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras, equipamentos=get_equipamentos()
            )

        elif g.acao == 'excluir' and g.bloco == 2:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)

            equipamento = db.get_or_404(Equipamentos, id_equipamento)
            try:
                db.session.delete(equipamento)

                db.session.flush()
                registrar_log_generico_usuario(g.userid, 'Exclusão', equipamento)

                db.session.commit()
                flash("Equipamento deletado com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao deletar equipamento")
            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras, equipamentos=get_equipamentos()
            )

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/equipamentos.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)