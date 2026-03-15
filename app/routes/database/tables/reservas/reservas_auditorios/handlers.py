from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string, parse_date_string_or_abort
from app.dao.internal.aulas import get_aulas_ativas
from app.dao.internal.locais import get_locais
from app.dao.internal.reservas import get_reservas_auditorios_database
from app.dao.internal.usuarios import get_pessoas
from app.decorators.decorators import register_handler
from app.enums import StatusReservaAuditorioEnum
from app.extensions import db
from app.models.reservas.reservas_auditorios import Reservas_Auditorios
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_reservas = select(Reservas_Auditorios)
    reservas_auditorios_paginadas = SelectPagination(
        select=sel_reservas, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['reservas_auditorios'] = reservas_auditorios_paginadas.items
    g.extras['pagination'] = reservas_auditorios_paginadas

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['pessoas'] = get_pessoas()
    g.extras['locais'] = get_locais()
    g.extras['aulas_ativas'] = get_aulas_ativas()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
    id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
    dia_reserva = parse_date_string(request.form.get('dia_reserva'))
    status_reserva = none_if_empty(request.form.get('status_reserva'),)
    id_autorizador = none_if_empty(request.form.get('id_autorizador'), int)
    observação_responsavel = none_if_empty(request.form.get('observação_responsavel'))
    observação_autorizador = none_if_empty(request.form.get('observação_autorizador'))
    filters = []
    query_params = get_query_params(request)
    if id_reserva_auditorio is not None:
        filters.append(Reservas_Auditorios.id_reserva_auditorio == id_reserva_auditorio)
    if id_responsavel is not None:
        filters.append(Reservas_Auditorios.id_responsavel == id_responsavel)
    if id_reserva_local is not None:
        filters.append(Reservas_Auditorios.id_reserva_local == id_reserva_local)
    if id_reserva_aula is not None:
        filters.append(Reservas_Auditorios.id_reserva_aula == id_reserva_aula)
    if dia_reserva:
        filters.append(Reservas_Auditorios.dia_reserva == dia_reserva)
    if status_reserva:
        filters.append(Reservas_Auditorios.status_reserva == StatusReservaAuditorioEnum(status_reserva))
    if id_autorizador is not None:
        filters.append(Reservas_Auditorios.id_autorizador == id_autorizador)
    if observação_responsavel:
        filters.append(Reservas_Auditorios.observação_responsavel.ilike(f"%{observação_responsavel}%"))
    if observação_autorizador:
        filters.append(Reservas_Auditorios.observação_autorizador.ilike(f"%{observação_autorizador}"))
    if filters:
        sel_reservas = select(Reservas_Auditorios).where(*filters)
        reservas_auditorios_paginadas = SelectPagination(
        select=sel_reservas, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
        g.extras['reservas_auditorios'] = reservas_auditorios_paginadas.items
        g.extras['pagination'] = reservas_auditorios_paginadas
        g.extras['query_params'] = query_params
    else:
        flash("especifique ao menos um campo", "danger")
        g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
            pessoas=get_pessoas(), locais=get_locais(), aulas_ativas=get_aulas_ativas()
    )

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['pessoas'] = get_pessoas()
    g.extras['locais'] = get_locais()
    g.extras['aulas_ativas'] = get_aulas_ativas()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
    id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
    dia_reserva = parse_date_string(request.form.get('dia_reserva'))
    status_reserva = none_if_empty(request.form.get('status_reserva'))
    id_autorizador = none_if_empty(request.form.get('id_autorizador'), int)
    observacao_responsavel = none_if_empty(request.form.get('observação_responsavel'))
    observacao_autorizador = none_if_empty(request.form.get('observação_autorizador'))

    nova_reserva = Reservas_Auditorios(
        id_responsavel=id_responsavel,
        id_reserva_local=id_reserva_local,
        id_reserva_aula=id_reserva_aula,
        dia_reserva=dia_reserva,
        status_reserva=StatusReservaAuditorioEnum(status_reserva),
        id_autorizador=id_autorizador,
        observação_responsavel=observacao_responsavel,
        observação_autorizador=observacao_autorizador
    )

    db_action(
        "Inserção",
        "Reserva cadastrada com sucesso",
        "Erro ao cadastrar reserva",
        obj=nova_reserva
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        pessoas=get_pessoas(),
        locais=get_locais(),
        aulas_ativas=get_aulas_ativas()
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_reservas_auditorios():
    g.extras['reservas_auditorios'] = get_reservas_auditorios_database()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_reserva_auditorio():
    id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
    reserva_auditorio = db.get_or_404(Reservas_Auditorios, id_reserva_auditorio)
    g.extras['reserva_auditorio'] = reserva_auditorio
    g.extras['pessoas'] = get_pessoas()
    g.extras['locais'] = get_locais()
    g.extras['aulas_ativas'] = get_aulas_ativas()

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
    id_responsavel = get_value_or_abort(request.form.get('id_responsavel'), 400, "id do responsavel é obrigatorio", int)
    id_reserva_local = get_value_or_abort(request.form.get('id_reserva_local'), 400, "id do local é obrigatorio", int)
    id_reserva_aula = get_value_or_abort(request.form.get('id_reserva_aula'), 400, "id da aula é obrigatorio", int)
    dia_reserva = parse_date_string_or_abort(request.form.get('dia_reserva'), 400, "dia da reserva é obrigatorio")
    status_reserva = none_if_empty(request.form.get('status_reserva'))
    id_autorizador = none_if_empty(request.form.get('id_autorizador'), int)
    observacao_responsavel = none_if_empty(request.form.get('observação_responsavel'))
    observacao_autorizador = none_if_empty(request.form.get('observação_autorizador'))

    reserva_auditorio = db.get_or_404(Reservas_Auditorios, id_reserva_auditorio)
    dados_anteriores = copy(reserva_auditorio)

    def update():
        reserva_auditorio.id_responsavel = id_responsavel
        reserva_auditorio.id_reserva_local = id_reserva_local
        reserva_auditorio.id_reserva_aula = id_reserva_aula
        reserva_auditorio.dia_reserva = dia_reserva
        reserva_auditorio.status_reserva = StatusReservaAuditorioEnum(status_reserva)
        reserva_auditorio.id_autorizador = id_autorizador
        reserva_auditorio.observação_responsavel = observacao_responsavel
        reserva_auditorio.observação_autorizador = observacao_autorizador

    db_action(
        "Edição",
        "Reserva editada com sucesso",
        "Erro ao editar reserva",
        obj=reserva_auditorio,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        reservas_auditorios=get_reservas_auditorios_database()
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_fetch():
    id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)

    reserva_auditorio = db.get_or_404(Reservas_Auditorios, id_reserva_auditorio)

    db_action(
        "Exclusão",
        "Reserva excluida com sucesso",
        "Erro ao excluir reserva",
        obj=reserva_auditorio
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        reservas_auditorios=get_reservas_auditorios_database()
    )