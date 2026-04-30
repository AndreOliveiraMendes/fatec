from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import and_, select

from app.auxiliar.dao_query import filtro_tipo_responsavel
from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string, parse_date_string_or_abort
from app.dao.internal.aulas import get_aulas_ativas
from app.dao.internal.locais import get_locais
from app.dao.internal.reservas import (check_reserva_temporaria,
                                       get_reservas_temporarias)
from app.decorators.decorators import register_handler
from app.enums import FinalidadeReservaEnum
from app.extensions import db
from app.models.reservas.reservas_laboratorios import Reservas_Temporarias
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

def filtro_intervalo(inicio_procura, fim_procura):
    if inicio_procura and fim_procura:
        return and_(
            Reservas_Temporarias.fim_reserva >= inicio_procura,
            Reservas_Temporarias.inicio_reserva <= fim_procura
        )
    elif inicio_procura:
        return Reservas_Temporarias.fim_reserva >= inicio_procura
    elif fim_procura:
        return Reservas_Temporarias.inicio_reserva <= fim_procura
    else:
        raise ValueError("Especifique ao menos um valor")
    
@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_reservas = select(Reservas_Temporarias)
    reservas_temporarias_paginadas = SelectPagination(
        select=sel_reservas, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['reservas_temporarias'] = reservas_temporarias_paginadas.items
    g.extras['pagination'] = reservas_temporarias_paginadas

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['locais'] = get_locais()
    g.extras['aulas_ativas'] = get_aulas_ativas()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
    tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
    id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
    id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
    inicio_procura = parse_date_string(request.form.get('inicio_procura'))
    fim_procura = parse_date_string(request.form.get('fim_procura'))
    finalidade_reserva = none_if_empty(request.form.get('finalidade_reserva'))
    observacoes = none_if_empty(request.form.get('observacoes'))
    descricao = none_if_empty(request.form.get('descricao'))
    filters = []
    query_params = get_query_params(request)
    if id_reserva_temporaria is not None:
        filters.append(Reservas_Temporarias.id_reserva_temporaria == id_reserva_temporaria)
    if id_responsavel is not None:
        filters.append(Reservas_Temporarias.id_responsavel == id_responsavel)
    if id_responsavel_especial is not None:
        filters.append(Reservas_Temporarias.id_responsavel_especial == id_responsavel_especial)
    if tipo_responsavel is not None:
        filters.append(filtro_tipo_responsavel(Reservas_Temporarias, tipo_responsavel))
    if id_reserva_local is not None:
        filters.append(Reservas_Temporarias.id_reserva_local == id_reserva_local)
    if id_reserva_aula is not None:
        filters.append(Reservas_Temporarias.id_reserva_aula == id_reserva_aula)
    if inicio_procura or fim_procura:
        filters.append(filtro_intervalo(inicio_procura, fim_procura))
    if finalidade_reserva:
        filters.append(Reservas_Temporarias.finalidade_reserva == FinalidadeReservaEnum(finalidade_reserva))
    if observacoes:
        filters.append(Reservas_Temporarias.observacoes.ilike(f"%{observacoes}%"))
    if descricao:
        filters.append(Reservas_Temporarias.descricao.ilike(f"%{descricao}%"))
    if filters:
        sel_reservas = select(Reservas_Temporarias).where(*filters)
        reservas_temporarias_paginadas = SelectPagination(
            select=sel_reservas, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['reservas_temporarias'] = reservas_temporarias_paginadas.items
        g.extras['pagination'] = reservas_temporarias_paginadas
        g.extras['query_params'] = query_params
    else:
        flash("especifique ao menos um campo de busca", "danger")
        g.redirect_action, g.bloco = register_return(g.url,
            g.acao, g.extras,
            locais=get_locais(),
            aulas_ativas=get_aulas_ativas()
        )

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['locais'] = get_locais()
    g.extras['aulas_ativas'] = get_aulas_ativas()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
    id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
    id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
    inicio_reserva = parse_date_string(request.form.get('inicio_reserva'))
    fim_reserva = parse_date_string(request.form.get('fim_reserva'))
    finalidade_reserva = none_if_empty(request.form.get('finalidade_reserva'))
    observacoes = none_if_empty(request.form.get('observacoes'))
    descricao = none_if_empty(request.form.get('descricao'))

    nova_reserva_temporaria = Reservas_Temporarias(
        id_responsavel=id_responsavel,
        id_responsavel_especial=id_responsavel_especial,
        id_reserva_local=id_reserva_local,
        id_reserva_aula=id_reserva_aula,
        inicio_reserva=inicio_reserva,
        fim_reserva=fim_reserva,
        finalidade_reserva=FinalidadeReservaEnum(finalidade_reserva),
        observacoes=observacoes,
        descricao=descricao
    )

    def insert():
        check_reserva_temporaria(
            inicio_reserva,
            fim_reserva,
            id_reserva_local,
            id_reserva_aula
        )

    db_action(
        "Inserção",
        "Reserva temporaria cadastrada com sucesso",
        "Erro ao cadastrar reserva",
        obj=nova_reserva_temporaria,
        action=insert
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        locais=get_locais(),
        aulas_ativas=get_aulas_ativas()
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_reservas_temporarias():
    g.extras['reservas_temporarias'] = get_reservas_temporarias()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_reserva_temporaria():
    id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)
    reserva_temporaria = db.get_or_404(Reservas_Temporarias, id_reserva_temporaria)
    g.extras['reserva_temporaria'] = reserva_temporaria
    g.extras['locais'] = get_locais()
    g.extras['aulas_ativas'] = get_aulas_ativas()

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
    id_reserva_local = get_value_or_abort(request.form.get('id_reserva_local'), 400, "id do local é obrigatorio", int)
    id_reserva_aula = get_value_or_abort(request.form.get('id_reserva_aula'), 400, "id da aula é obrigatorio", int)
    inicio_reserva = parse_date_string_or_abort(request.form.get('inicio_reserva'), 400, "data de inicio é obrigatoria")
    fim_reserva = parse_date_string_or_abort(request.form.get('fim_reserva'), 400, "data de termino é obrigatorio")
    finalidade_reserva = none_if_empty(request.form.get('finalidade_reserva'))
    observacoes = none_if_empty(request.form.get('observacoes'))
    descricao = none_if_empty(request.form.get('descricao'))

    reserva_temporaria = db.get_or_404(Reservas_Temporarias, id_reserva_temporaria)
    dados_anteriores = copy(reserva_temporaria)

    def update():
        check_reserva_temporaria(
            inicio_reserva,
            fim_reserva,
            id_reserva_local,
            id_reserva_aula,
            id_reserva_temporaria
        )

        reserva_temporaria.id_responsavel = id_responsavel
        reserva_temporaria.id_responsavel_especial = id_responsavel_especial
        reserva_temporaria.id_reserva_local = id_reserva_local
        reserva_temporaria.id_reserva_aula = id_reserva_aula
        reserva_temporaria.inicio_reserva = inicio_reserva
        reserva_temporaria.fim_reserva = fim_reserva
        reserva_temporaria.finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva)
        reserva_temporaria.observacoes = observacoes
        reserva_temporaria.descricao = descricao

    db_action(
        "Edição",
        "Reserva editada com sucesso",
        "Erro ao editar reserva",
        obj=reserva_temporaria,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        reservas_temporarias=get_reservas_temporarias()
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)

    reserva_temporaria = db.get_or_404(Reservas_Temporarias, id_reserva_temporaria)

    db_action(
        "Exclusão",
        "Reserva excluida com sucesso",
        "Erro ao excluir reserva",
        obj=reserva_temporaria
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        reservas_temporarias=get_reservas_temporarias()
    )