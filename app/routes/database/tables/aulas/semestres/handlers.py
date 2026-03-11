import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string, parse_date_string_or_abort
from app.dao.internal.aulas import get_semestres
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.aulas import Semestres
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from app.service.aulas_service import check_semestre
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_hanler():
    sel_semestres = select(Semestres)
    semestres_paginados = SelectPagination(
        select=sel_semestres, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['semestres'] = semestres_paginados.items
    g.extras['pagination'] = semestres_paginados

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_semestre = none_if_empty(request.form.get('id_semestre'), int)
    nome_semestre = none_if_empty(request.form.get('nome_semestre'))
    emnome_semestre = 'emnome_semestre' in request.form
    data_inicio = parse_date_string(request.form.get('data_inicio'))
    data_fim = parse_date_string(request.form.get('data_fim'))
    data_inicio_reserva = parse_date_string(request.form.get('data_inicio_reserva'))
    data_fim_reserva = parse_date_string(request.form.get('data_fim_reserva'))
    dias_de_prioridade = none_if_empty(request.form.get('prioridade'), int)
    filters = []
    query_params = get_query_params(request)
    if id_semestre is not None:
        filters.append(Semestres.id_semestre == id_semestre)
    if nome_semestre:
        if emnome_semestre:
            filters.append(Semestres.nome_semestre == nome_semestre)
        else:
            filters.append(Semestres.nome_semestre.ilike(f"%{nome_semestre}%"))
    if data_inicio:
        filters.append(Semestres.data_inicio == data_inicio)
    if data_fim:
        filters.append(Semestres.data_fim == data_fim)
    if data_inicio_reserva:
        filters.append(Semestres.data_inicio_reserva == data_inicio_reserva)
    if data_fim_reserva:
        filters.append(Semestres.data_fim_reserva == data_fim_reserva)
    if dias_de_prioridade is not None:
        filters.append(Semestres.dias_de_prioridade == dias_de_prioridade)
    if filters:
        sel_semestres = select(Semestres).where(*filters)
        semestres_paginados = semestres_paginados = SelectPagination(
            select=sel_semestres, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['semestres'] = semestres_paginados.items
        g.extras['pagination'] = semestres_paginados
        g.extras['query_params'] = query_params
    else:
        flash("especifique pelo menos um campo de busca", "danger")
        g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras)

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    nome_semestre = none_if_empty(request.form.get('nome_semestre'))
    data_inicio = parse_date_string(request.form.get('data_inicio'))
    data_fim = parse_date_string(request.form.get('data_fim'))
    data_inicio_reserva = parse_date_string(request.form.get('data_inicio_reserva'))
    data_fim_reserva = parse_date_string(request.form.get('data_fim_reserva'))
    dias_de_prioridade = none_if_empty(request.form.get('prioridade'), int)

    novo_semestre = Semestres(
        nome_semestre=nome_semestre,
        data_inicio=data_inicio,
        data_fim=data_fim,
        data_inicio_reserva=data_inicio_reserva,
        data_fim_reserva=data_fim_reserva,
        dias_de_prioridade=dias_de_prioridade
    )

    def insert():
        check_semestre(data_inicio, data_fim)
        db.session.add(novo_semestre)

    db_action(
        "Inserção",
        "Semestre cadastrado com sucesso",
        "Erro ao cadastrar semestre",
        obj=novo_semestre,
        action=insert
    )

    g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras)

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_semestres():
    g.extras['semestres'] = get_semestres()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_semestre():
    id_semestre = none_if_empty(request.form.get('id_semestre'), int)
    semestre = db.get_or_404(Semestres, id_semestre)
    g.extras['semestre'] = semestre

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_semestre = none_if_empty(request.form.get('id_semestre'), int)
    nome_semestre = get_value_or_abort(request.form.get('nome_semestre'), 400, "nome do semestre é obrigatorio")
    data_inicio = parse_date_string_or_abort(request.form.get('data_inicio'), 400, "data de inicio obrigatoria")
    data_fim = parse_date_string_or_abort(request.form.get('data_fim'), 400, "data de termino obrigatoria")
    data_inicio_reserva = parse_date_string_or_abort(request.form.get('data_inicio_reserva'), 400, "data de inicio de cadastro obrigatoria")
    data_fim_reserva = parse_date_string_or_abort(request.form.get('data_fim_reserva'), 400, "data de fim de cadastro obrigatoria")
    dias_de_prioridade = get_value_or_abort(request.form.get('prioridade'), 400, "dias de prioridade obrigatorio", int)

    semestre = db.get_or_404(Semestres, id_semestre)
    dados_anteriores = copy.copy(semestre)

    def update():
        check_semestre(data_inicio, data_fim, id_semestre)

        semestre.nome_semestre = nome_semestre
        semestre.data_inicio = data_inicio
        semestre.data_fim = data_fim
        semestre.data_inicio_reserva = data_inicio_reserva
        semestre.data_fim_reserva = data_fim_reserva
        semestre.dias_de_prioridade = dias_de_prioridade

    db_action(
        "Edição",
        "Semestre editado com sucesso",
        "Erro ao editar semestre",
        obj=semestre,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        semestres=get_semestres()
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_semestre = none_if_empty(request.form.get('id_semestre'), int)

    semestre = db.get_or_404(Semestres, id_semestre)

    def delete():
        db.session.delete(semestre)

    db_action(
        "Exclusão",
        "Semestre excluido com sucesso",
        "Erro ao excluir semestre",
        obj=semestre,
        action=delete
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        semestres=get_semestres()
    )