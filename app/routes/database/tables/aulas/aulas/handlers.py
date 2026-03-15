from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_time_string, parse_time_string_or_abort
from app.dao.internal.aulas import get_aulas
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.aulas import Aulas
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, "listar", 0)
def list_handler():
    sel_aulas = select(Aulas)
    aulas_paginadas = SelectPagination(
        select=sel_aulas, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['aulas'] = aulas_paginadas.items
    g.extras['pagination'] = aulas_paginadas

@register_handler(dispatcher, "procurar", 1)
def search_fetch():
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

@register_handler(dispatcher, "inserir", 1)
def insert_push():
    horario_inicio = parse_time_string(request.form.get('horario_inicio'))
    horario_fim = parse_time_string(request.form.get('horario_fim'))

    nova_aula = Aulas(
        horario_inicio=horario_inicio,
        horario_fim=horario_fim
    )

    db_action(
        "Inserção",
        "Aula cadastrada com sucesso",
        "Erro ao cadastrar aula",
        obj=nova_aula
    )

    g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras)

@register_handler(dispatcher, "editar", 0)
@register_handler(dispatcher, "excluir", 0)
def fetch_aulas():
    g.extras['aulas'] = get_aulas()

@register_handler(dispatcher, "editar", 1)
@register_handler(dispatcher, "excluir", 1)
def fetch_aula():
    id_aula = none_if_empty(request.form.get('id_aula'), int)
    aula = db.get_or_404(Aulas, id_aula)
    g.extras['aula'] = aula

@register_handler(dispatcher, "editar", 2)
def edit_push():
    id_aula = none_if_empty(request.form.get('id_aula'), int)

    horario_inicio = parse_time_string_or_abort(
        request.form.get('horario_inicio'),
        400,
        "horario de inicio é obrigatorio"
    )

    horario_fim = parse_time_string_or_abort(
        request.form.get('horario_fim'),
        400,
        "horario de fim é obrigatorio"
    )

    aula = db.get_or_404(Aulas, id_aula)

    dados_anteriores = copy(aula)

    def action():
        aula.horario_inicio = horario_inicio
        aula.horario_fim = horario_fim

    db_action(
        "Edição",
        "Aula editada com sucesso",
        "Erro ao editar aula",
        obj=aula,
        old_obj=dados_anteriores,
        action=action
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        aulas=get_aulas()
    )

@register_handler(dispatcher, "excluir", 2)
def exclude_push():
    id_aula = none_if_empty(request.form.get('id_aula'), int)

    aula = db.get_or_404(Aulas, id_aula)

    db_action(
        "Exclusão",
        "Aula excluida com sucesso",
        "Erro ao excluir aula",
        obj=aula
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        aulas=get_aulas()
    )