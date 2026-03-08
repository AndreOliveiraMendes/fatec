import copy
from typing import Any

from flask import Blueprint, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_categorias
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.equipamentos import Categorias_de_Equipamentos
from app.routes_helper.request import get_query_params, get_session_or_request
from config.database_views import get_url
from config.general import PER_PAGE

bp = Blueprint('database_categorias_de_equipamentos', __name__, url_prefix="/database")

@bp.route("/categorias_de_equipamentos", methods=["GET", "POST"])
@admin_required
def gerenciar_categorias_de_equipamentos():
    url = get_url('database_categorias_de_equipamentos')
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {'url':url}
    if request.method == 'POST':
        if acao == "listar":
            sel_categorias = select(Categorias_de_Equipamentos)
            categorias_paginas = SelectPagination(
                select=sel_categorias, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['categorias'] = categorias_paginas.items
            extras['pagination'] = categorias_paginas

        elif acao == "procurar" and bloco == 1:
            id_categoria = none_if_empty(request.form.get('id_categoria'))
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
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['categorias'] = categorias_paginas.items
                extras['pagination'] = categorias_paginas
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(
                    url, acao, extras
                )
        
        elif acao == "inserir" and bloco == 1:
            nome_categoria = none_if_empty(request.form.get('nome_categoria'))
            descricao = none_if_empty(request.form.get('descricao'))

            try:
                nova_categoria = Categorias_de_Equipamentos(
                    nome_categoria = nome_categoria,
                    descricao = descricao
                )
                db.session.add(nova_categoria)
                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_categoria)
                db.session.commit()
                flash("categoria cadastrada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "erro ao cadastrar categoria")
            redirect_action, bloco = register_return(
                url, acao, extras
            )

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['categorias'] = get_categorias()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_categoria = none_if_empty(request.form.get('id_categoria'))
            categoria = db.get_or_404(Categorias_de_Equipamentos, id_categoria)
            extras['categoria'] = categoria
        elif acao == 'editar' and bloco == 2:
            id_categoria = none_if_empty(request.form.get('id_categoria'))
            nome_categoria = get_value_or_abort(request.form.get('nome_categoria'), 400, "nome é obrigatorio")
            descricao = none_if_empty(request.form.get('descricao'))

            categoria = db.get_or_404(Categorias_de_Equipamentos, id_categoria)
            try:
                dados_anteriores = copy.copy(categoria)

                categoria.nome_categoria = nome_categoria
                categoria.descricao = descricao

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', categoria, dados_anteriores)

                db.session.commit()
                flash("Categoria editada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar categoria")
            redirect_action, bloco = register_return(
                url, acao, extras, categorias=get_categorias()
            )
        
        elif acao == 'excluir' and bloco == 2:
            id_categoria = none_if_empty(request.form.get('id_categoria'))

            categoria = db.get_or_404(Categorias_de_Equipamentos, id_categoria)
            try:
                db.session.delete(categoria)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', categoria)

                db.session.commit()
                flash("Categoria excluida com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao excluir categoria")
            redirect_action, bloco = register_return(
                url, acao, extras, categorias=get_categorias()
            )

    if redirect_action:
        return redirect_action
    return render_template("database/table/categorias_de_equipamento.html",
        user=user, acao=acao, bloco=bloco, **extras)