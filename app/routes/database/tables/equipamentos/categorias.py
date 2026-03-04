from typing import Any

from flask import (Blueprint, flash, redirect, render_template,
                   request, session, url_for)
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.general import _handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.models.equipamentos import Categorias_de_Equipamentos
from app.routes_helper.request import get_session_or_request
from app.extensions import db
from config.general import PER_PAGE

bp = Blueprint('database_categorias_de_equipamentos', __name__, url_prefix="/database")

@bp.route("/categorias_de_equipamentos", methods=["GET", "POST"])
@admin_required
def gerenciar_categorias_de_equipamentos():
    url = 'database_categorias_de_equipamentos.gerenciar_categorias_de_equipamentos'
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
            extras['pagination']
        
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
                _handle_db_error(e, "erro ao cadastrar categoria")
            redirect_action, bloco = register_return(
                url, acao, extras
            )
    if redirect_action:
        return redirect_action
    return render_template("database/table/categorias_de_equipamento.html",
        user=user, acao=acao, bloco=bloco, **extras)