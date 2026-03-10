import copy

from flask import Blueprint, abort, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.aulas import get_dias_da_semana
from app.decorators.decorators import admin_required, crud_route
from app.extensions import db
from app.models.aulas import Dias_da_Semana
from app.routes_helper.db_actions import db_action
from app.routes_helper.ui import disable_action
from config.general import PER_PAGE

bp = Blueprint('database_dias_da_semana', __name__, url_prefix="/database")

@bp.route("/dias_da_semana", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_dias_da_semana():
    disabled = ['procurar']
    disable_action(g.extras, disabled)
    if request.method == 'POST':
        if g.acao in disabled:
            abort(403, description="Esta funcionalidade não foi implementada.")

        if g.acao == 'listar':
            sel_dias_semana = select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
            dias_da_semana_paginada = SelectPagination(
                select=sel_dias_semana, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['dias_da_semana'] = dias_da_semana_paginada.items
            g.extras['pagination'] = dias_da_semana_paginada

        elif g.acao == 'inserir' and g.bloco == 1:
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            nome_semana = none_if_empty(request.form.get('nome_semana', None))

            nova_semana = Dias_da_Semana(
                id_semana=id_semana,
                nome_semana=nome_semana
            )

            def insert():
                db.session.add(nova_semana)

            db_action(
                "Inserção",
                "Semana cadastrada com sucesso",
                "Falha ao cadastrar semana",
                obj=nova_semana,
                action=insert
            )

            g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras)

        elif g.acao in ['editar', 'excluir'] and g.bloco == 0:
            g.extras['dias_da_semana'] = get_dias_da_semana()
        elif g.acao in ['editar', 'excluir'] and g.bloco == 1:
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            dia_da_semana = db.get_or_404(Dias_da_Semana, id_semana)
            g.extras['dia_semana'] = dia_da_semana
        elif g.acao == 'editar' and g.bloco == 2:
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            nome_semana = get_value_or_abort(request.form.get('nome_semana'), 400, "Nome do dia da semana é obrigatório.")
            dia_da_semana = db.get_or_404(Dias_da_Semana, id_semana)

            dados_anteriores = copy.copy(dia_da_semana)

            def update():
                dia_da_semana.nome_semana = nome_semana

            db_action(
                "Edição",
                "Dia da semana editado com sucesso",
                "Falha ao editar semana",
                obj=dia_da_semana,
                old_obj=dados_anteriores,
                action=update
            )

            g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras, dias_da_semana=get_dias_da_semana())
        elif g.acao == 'excluir' and g.bloco == 2:
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            dia_da_semana = db.get_or_404(Dias_da_Semana, id_semana)

            def delete():
                db.session.delete(dia_da_semana)

            db_action(
                "Exclusão",
                "Dia da semana excluido com sucesso",
                "falha ao excluir semana",
                obj=dia_da_semana,
                action=delete
            )

            g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras, dias_da_semana=get_dias_da_semana())
    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/dias_da_semana.html", user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)