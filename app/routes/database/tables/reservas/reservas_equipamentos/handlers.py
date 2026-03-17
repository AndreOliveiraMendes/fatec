from datetime import datetime

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
from app.routes_helper.db_actions import db_action
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
    id_reserva_responsavel = none_if_empty(request.form.get('id_reserva_responsavel'), int)
    data_reserva = parse_date_string(request.form.get('data_reserva'))
    estado = none_if_empty(request.form.get('estado'))
    estado_enum = None
    cancelado_por_id = none_if_empty(request.form.get('cancelado_por_id'), int)
    cancelado_em = parse_datetime_string(request.form.get('cancelado_em'))
    motivo_cancelamento = none_if_empty(request.form.get('motivo_cancelamento'))
    try:
        estado_enum = StatusReservaEquipamentoEnum(estado)
    except ValueError as e:
        estado_enum = None
    filters = []
    query_params = get_query_params(request)
    if id_reserva:
        filters.append(Reservas_Equipamentos.id_reserva == id_reserva)
    if id_reserva_aula:
        filters.append(Reservas_Equipamentos.id_reserva_aula == id_reserva_aula)
    if id_reserva_responsavel:
        filters.append(Reservas_Equipamentos.id_reserva_responsavel == id_reserva_responsavel)
    if data_reserva:
        filters.append(Reservas_Equipamentos.data_reserva == data_reserva)
    if estado_enum:
        filters.append(Reservas_Equipamentos.estado == estado_enum)
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


@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['aulas_ativas'] = get_aulas_ativas()
    g.extras['pessoas'] = get_pessoas()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
    id_reserva_responsavel = none_if_empty(request.form.get('id_reserva_responsavel'), int)
    data_reserva = parse_date_string(request.form.get('data_reserva'))
    cancelado_por_id = none_if_empty(request.form.get('cancelado_por_id'), int)
    cancelado_em = parse_datetime_string(request.form.get('cancelado_em'))
    estado = none_if_empty(request.form.get('estado'))
    motivo_cancelamento = none_if_empty(request.form.get('motivo_cancelamento'))

    nova_reserva = Reservas_Equipamentos(
        id_reserva_aula = id_reserva_aula,
        id_reserva_responsavel = id_reserva_responsavel,
        data_reserva = data_reserva
    )

    def inserir():
        nova_reserva.estado = StatusReservaEquipamentoEnum(estado)
        if nova_reserva.estado == StatusReservaEquipamentoEnum.CANCELADA:
            if not cancelado_por_id:
                raise ValueError("Cancelamento precisa de responsável")
            nova_reserva.cancelado_por_id = cancelado_por_id
            if cancelado_em:
                nova_reserva.cancelado_em = cancelado_em
            else:
                nova_reserva.cancelado_em = datetime.now()
            nova_reserva.motivo_cancelamento = motivo_cancelamento

    def post_inserir():
        if nova_reserva.cancelado_em and nova_reserva.cancelado_em < nova_reserva.criado_em:
            raise ValueError("Cancelamento não pode ser antes da criação")

    db_action(
        "Inserção",
        "Reserva inserida com sucesso",
        "Erro ao inserir reserva",
        obj=nova_reserva,
        action=inserir,
        post_action=post_inserir
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        aulas_ativas = get_aulas_ativas(),
        pessoas = get_pessoas()
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_reservas_fixas():
    pass

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_reserva_fixa():
    g.extras['aulas_ativas'] = get_aulas_ativas()
    g.extras['pessoas'] = get_pessoas()

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    pass

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    pass
