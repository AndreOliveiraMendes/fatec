import copy

from flask import Blueprint, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_time_string, parse_time_string_or_abort
from app.dao.internal.aulas import get_aulas
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.decorators.decorators import admin_required, crud_route
from app.extensions import db
from app.models.aulas import Aulas
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

bp = Blueprint('database_aulas', __name__, url_prefix="/database")

@bp.route("/aulas", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_aulas():
    if request.method == 'POST':
        if g.acao == 'listar':
            sel_aulas = select(Aulas)
            aulas_paginadas = SelectPagination(
                select=sel_aulas, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['aulas'] = aulas_paginadas.items
            g.extras['pagination'] = aulas_paginadas

        elif g.acao == 'procurar' and g.bloco == 1:
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            horario_inicio_start = parse_time_string(request.form.get('horario_inicio_start'))
            horario_inicio_end = parse_time_string(request.form.get('horario_inicio_end'))
            horario_fim_start = parse_time_string(request.form.get('horario_fim_start'))
            horario_fim_end = parse_time_string(request.form.get('horario_fim_end'))
            filters = []
            query_params = get_query_params(request)
            if id_aula is not None:
                filters.append(Aulas.id_aula == id_aula)
            if horario_inicio_start or horario_inicio_end:
                if horario_inicio_start and horario_inicio_end:
                    filters.append(Aulas.horario_inicio.between(horario_inicio_start, horario_inicio_end))
                elif horario_inicio_start:
                    filters.append(Aulas.horario_inicio >= horario_inicio_start)
                else:
                    filters.append(Aulas.horario_inicio <= horario_inicio_end)
            if horario_fim_start or horario_fim_end:
                if horario_fim_start and horario_fim_end:
                    filters.append(Aulas.horario_fim.between(horario_fim_start, horario_fim_end))
                elif horario_fim_start:
                    filters.append(Aulas.horario_fim >= horario_fim_start)
                else:
                    filters.append(Aulas.horario_fim <= horario_fim_end)
            if filters:
                sel_aulas = select(Aulas).where(*filters)
                aulas_paginadas = SelectPagination(
                    select=sel_aulas, session=db.session,
                    page=g.page, per_page=PER_PAGE, error_out=False
                )
                g.extras['aulas'] = aulas_paginadas.items
                g.extras['pagination'] = aulas_paginadas
                g.extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras)

        elif g.acao == 'inserir' and g.bloco == 1:
            horario_inicio = parse_time_string(request.form.get('horario_inicio'))
            horario_fim = parse_time_string(request.form.get('horario_fim'))
            try:
                nova_aula = Aulas(horario_inicio=horario_inicio, horario_fim=horario_fim)
                db.session.add(nova_aula)
                db.session.flush()
                registrar_log_generico_usuario(g.userid, "Inserção", nova_aula)
                db.session.commit()
                flash("Aula cadastrada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao cadastrar aula")
            g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras)

        elif g.acao in ['editar', 'excluir'] and g.bloco == 0:
            g.extras['aulas'] = get_aulas()
        elif g.acao in ['editar', 'excluir'] and g.bloco == 1:
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            aula = db.get_or_404(Aulas, id_aula)
            g.extras['aula'] = aula
        elif g.acao == 'editar' and g.bloco == 2:
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            horario_inicio = parse_time_string_or_abort(request.form.get('horario_inicio'), 400, "horario de inicio é obrigatorio")
            horario_fim = parse_time_string_or_abort(request.form.get('horario_fim'), 400, "horario de fim é obrigatorio")
            aula = db.get_or_404(Aulas, id_aula)
            try:
                dados_anteriores = copy.copy(aula)
                aula.horario_inicio = horario_inicio
                aula.horario_fim = horario_fim

                db.session.flush()
                registrar_log_generico_usuario(g.userid, "Edição", aula, dados_anteriores)

                db.session.commit()
                flash("Aula editada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar aula")

            g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras, aulas=get_aulas())
        elif g.acao == 'excluir' and g.bloco == 2:
            id_aula = none_if_empty(request.form.get('id_aula'), int)

            aula = db.get_or_404(Aulas, id_aula)
            try:
                db.session.delete(aula)

                db.session.flush()
                registrar_log_generico_usuario(g.userid, "Exclusão", aula)

                db.session.commit()
                flash("Aula excluida com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao excluir aula")

            g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras, aulas=get_aulas())
    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/aulas.html", user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)