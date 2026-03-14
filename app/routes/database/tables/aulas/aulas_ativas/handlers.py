from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.dao_query import filtro_intervalo
from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import (get_aulas, get_aulas_ativas,
                                    get_dias_da_semana)
from app.decorators.decorators import register_handler
from app.enums import TipoAulaEnum
from app.extensions import db
from app.models.aulas import Aulas_Ativas
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from app.service.aulas_service import check_aula_ativa
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_aulas_ativas = select(Aulas_Ativas)
    aulas_ativas_paginadas = SelectPagination(
        select=sel_aulas_ativas, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['aulas_ativas'] = aulas_ativas_paginadas.items
    g.extras['pagination'] = aulas_ativas_paginadas

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['aulas'] = get_aulas()
    g.extras['dias_da_semana'] = get_dias_da_semana()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
    id_aula = none_if_empty(request.form.get('id_aula'), int)
    inicio_procura = parse_date_string(request.form.get('inicio_procura'))
    fim_procura = parse_date_string(request.form.get('fim_procura'))
    id_semana = none_if_empty(request.form.get('id_semana'), int)
    tipo_aula = none_if_empty(request.form.get('tipo_aula'))
    filters = []
    query_params = get_query_params(request)
    if id_aula_ativa is not None:
        filters.append(Aulas_Ativas.id_aula_ativa == id_aula_ativa)
    if id_aula is not None:
        filters.append(Aulas_Ativas.id_aula == id_aula)
    if inicio_procura or fim_procura:
        filters.append(filtro_intervalo(inicio_procura, fim_procura))
    if id_semana is not None:
        filters.append(Aulas_Ativas.id_semana == id_semana)
    if tipo_aula:
        filters.append(Aulas_Ativas.tipo_aula == TipoAulaEnum(tipo_aula))
    if filters:
        sel_aulas_ativas = select(Aulas_Ativas).where(*filters)
        aulas_ativas_paginadas = SelectPagination(
            select=sel_aulas_ativas, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['aulas_ativas'] = aulas_ativas_paginadas.items
        g.extras['pagination'] = aulas_ativas_paginadas
        g.extras['query_params'] = query_params
    else:
        flash("especifique pelo menos um campo de busca", "danger")
        g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
            aulas=get_aulas(), dias_da_semana=get_dias_da_semana())

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['aulas'] = get_aulas()
    g.extras['dias_da_semana'] = get_dias_da_semana()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_aula = none_if_empty(request.form.get('id_aula'), int)
    inicio_ativacao = parse_date_string(request.form.get('inicio_ativacao'))
    fim_ativacao = parse_date_string(request.form.get('fim_ativacao'))
    id_semana = none_if_empty(request.form.get('id_semana'), int)
    tipo_aula = none_if_empty(request.form.get('tipo_aula'))

    nova_aula_ativa = Aulas_Ativas(
            id_aula = id_aula, inicio_ativacao = inicio_ativacao, fim_ativacao = fim_ativacao,
            id_semana = id_semana, tipo_aula = TipoAulaEnum(tipo_aula))

    def action():
        check_aula_ativa(inicio_ativacao, fim_ativacao, id_aula, id_semana, tipo_aula)
        db.session.add(nova_aula_ativa)

    db_action(
        "Inserção",
        "Aula ativa cadastrada com sucesso",
        "Erro ao cadastrar aula ativa",
        obj=nova_aula_ativa,
        action=action
    )

    g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
        aulas=get_aulas(), dias_da_semana=get_dias_da_semana())

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_aulas_ativas():
    g.extras['aulas_ativas'] = get_aulas_ativas()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_aula_ativa():
    id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
    aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)
    g.extras['aula_ativa'] = aula_ativa
    g.extras['aulas'] = get_aulas()
    g.extras['dias_da_semana'] = get_dias_da_semana()

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
    id_aula = get_value_or_abort(request.form.get('id_aula'), 400, "id_aula é obrigatório", int)
    inicio_ativacao = parse_date_string(request.form.get('inicio_ativacao'))
    fim_ativacao = parse_date_string(request.form.get('fim_ativacao'))
    id_semana = get_value_or_abort(request.form.get('id_semana'), 400, "id_semana é obrigatorio", int)
    tipo_aula = none_if_empty(request.form.get('tipo_aula'))
    aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)

    dados_anteriores = copy(aula_ativa)

    def action():
        check_aula_ativa(
            inicio_ativacao,
            fim_ativacao,
            id_aula,
            id_semana,
            tipo_aula,
            id_aula_ativa
        )

        aula_ativa.id_aula = id_aula
        aula_ativa.inicio_ativacao = inicio_ativacao
        aula_ativa.fim_ativacao = fim_ativacao
        aula_ativa.id_semana = id_semana
        aula_ativa.tipo_aula = TipoAulaEnum(tipo_aula)

    db_action(
        "Edição",
        "Aula ativa editada com sucesso",
        "Erro ao editar aula ativa",
        obj=aula_ativa,
        old_obj=dados_anteriores,
        action=action
    )

    g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
        aulas_ativas=get_aulas_ativas())

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
    aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)

    db_action(
        "Exclusão",
        "Aula ativa excluida com sucesso",
        "Erro ao excluir aula ativa",
        obj=aula_ativa,
        action=lambda: db.session.delete(aula_ativa)
    )

    g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
        aulas_ativas=get_aulas_ativas())