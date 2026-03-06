import copy
from typing import Any

from flask import Blueprint, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_categorias, get_equipamentos
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.equipamentos import Equipamentos
from app.routes_helper.request import get_query_params, get_session_or_request
from config.database_views import get_url
from config.general import PER_PAGE

bp = Blueprint('database_equipamentos', __name__, url_prefix="/database")

@bp.route("/equipamentos", methods=["GET", "POST"])
@admin_required
def gerenciar_equipamentos():
    url = get_url('database_equipamentos')
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {'url':url}
    if request.method == "POST":
        if acao == "listar":
            sel_equipamentos = select(Equipamentos)
            equipamentos_paginados = SelectPagination(
                select=sel_equipamentos, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras["equipamentos"] = equipamentos_paginados.items
            extras["pagination"] = equipamentos_paginados

        elif acao == "procurar" and bloco == 0:
            extras["categorias"] = get_categorias()
        elif acao == "procurar" and bloco == 1:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
            nome_equipamento = none_if_empty(request.form.get('nome_equipamento'))
            descricao = none_if_empty(request.form.get('descricao'))
            id_categoria = none_if_empty(request.form.get('id_categoria'), int)
            filter = []
            query_params = get_query_params(request)
            if id_equipamento is not None:
                filter.append(Equipamentos.id_equipamento == id_equipamento)
            if nome_equipamento:
                filter.append(Equipamentos.nome_equipamento.ilike(f"%{nome_equipamento}%"))
            if descricao:
                filter.append(Equipamentos.descricao.ilike(f"%{descricao}%"))
            if id_categoria is not None:
                filter.append(Equipamentos.id_categoria == id_categoria)
            if filter:
                sel_equipamentos = select(Equipamentos).where(
                    *filter
                )
                equipamentos_paginados = SelectPagination(
                    select=sel_equipamentos, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['equipamentos'] = equipamentos_paginados.items
                extras['pagination'] = equipamentos_paginados
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(
                    url, acao, extras, categorias=get_categorias()
                )

        elif acao == "inserir" and bloco == 0:
            extras["categorias"] = get_categorias()
        elif acao == "inserir" and bloco == 1:
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
                registrar_log_generico_usuario(userid, 'Inserção', novo_equipamento)

                db.session.commit()
                flash("Equipamento cadastrado com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao cadastrar equipamento")
            redirect_action, bloco = register_return(
                url, acao, extras, categorias=get_categorias()
            )

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras["equipamentos"] = get_equipamentos()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
            equipamento = db.get_or_404(Equipamentos, id_equipamento)
            extras['equipamento'] = equipamento
            extras['categorias'] = get_categorias()

        elif acao == 'editar' and bloco == 2:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
            nome_equipamento = none_if_empty(request.form.get('nome_equipamento'))
            descricao = none_if_empty(request.form.get('descricao'))
            id_categoria = none_if_empty(request.form.get('id_categoria'), int)

            equipamento = db.get_or_404(Equipamentos, id_equipamento)
            dados_anteriores = copy.copy(equipamento)
            try:
                equipamento.nome_equipamento = nome_equipamento
                equipamento.descricao = descricao
                equipamento.id_categoria = id_categoria

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', equipamento, dados_anteriores)

                db.session.commit()
                flash("Equipamento editado com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar equipamento")
            redirect_action, bloco = register_return(
                url, acao, extras, equipamentos=get_equipamentos()
            )

        elif acao == 'excluir' and bloco == 2:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)

            equipamento = db.get_or_404(Equipamentos, id_equipamento)
            try:
                db.session.delete(equipamento)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', equipamento)

                db.session.commit()
                flash("Equipamento deletado com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao deletar equipamento")
            redirect_action, bloco = register_return(
                url, acao, extras, equipamentos=get_equipamentos()
            )

    if redirect_action:
        return redirect_action
    return render_template("database/table/equipamentos.html",
        user=user, acao=acao, bloco=bloco, **extras)