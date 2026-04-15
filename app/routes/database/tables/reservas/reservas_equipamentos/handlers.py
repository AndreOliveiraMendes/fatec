from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string, parse_datetime_string
from app.dao.internal.aulas import get_aulas_ativas
from app.dao.internal.usuarios import get_pessoas
from app.decorators.decorators import register_handler
from app.enums import StatusReservaEquipamentoEnum
from app.extensions import db
from app.models.reservas.reservas_equipamentos import Reservas_Equipamentos
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_reservas = select(Reservas_Equipamentos)
    reservas_paginadas = SelectPagination(
        select=sel_reservas, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['reservas_equipamentos'] = reservas_paginadas.items
    g.extras['pagination'] = reservas_paginadas

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['aulas_ativas'] = get_aulas_ativas()
    g.extras['pessoas'] = get_pessoas()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_reserva = none_if_empty(request.form.get('id_reserva'), int)
    id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    data_reserva = parse_date_string(request.form.get('data_reserva'))
    status_reserva = none_if_empty(request.form.get('status_reserva'))
    status_reserva_enum = None
    cancelado_por_id = none_if_empty(request.form.get('cancelado_por_id'), int)
    cancelado_em = parse_datetime_string(request.form.get('cancelado_em'))
    motivo_cancelamento = none_if_empty(request.form.get('motivo_cancelamento'))
    try:
        status_reserva_enum = StatusReservaEquipamentoEnum(status_reserva)
    except ValueError as e:
        status_reserva_enum = None
    filters = []
    query_params = get_query_params(request)
    if id_reserva:
        filters.append(Reservas_Equipamentos.id_reserva == id_reserva)
    if id_reserva_aula:
        filters.append(Reservas_Equipamentos.id_reserva_aula == id_reserva_aula)
    if id_responsavel:
        filters.append(Reservas_Equipamentos.id_responsavel == id_responsavel)
    if data_reserva:
        filters.append(Reservas_Equipamentos.data_reserva == data_reserva)
    if status_reserva_enum:
        filters.append(Reservas_Equipamentos.status_reserva == status_reserva_enum)
    if cancelado_por_id:
        filters.append(Reservas_Equipamentos.cancelado_por_id == cancelado_por_id)
    if cancelado_em:
        filters.append(Reservas_Equipamentos.cancelado_em == cancelado_em)
    if motivo_cancelamento:
        filters.append(Reservas_Equipamentos.motivo_cancelamento == motivo_cancelamento)
    if filters:
        sel_reservas = select(Reservas_Equipamentos).where(
            *filters
        )
        reservas_paginadas = SelectPagination(
            select=sel_reservas, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['reservas_equipamentos'] = reservas_paginadas.items
        g.extras['pagination'] = reservas_paginadas
        g.extras['query_params'] = query_params
    else:
        flash("especifique ao menos um campo", "danger")
        g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
            aulas_ativas = get_aulas_ativas(), pessoas = get_pessoas()
    )