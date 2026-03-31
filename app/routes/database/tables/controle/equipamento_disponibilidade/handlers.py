
from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.equipamentos import get_equipamentos
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.controle import EquipamentoDisponibilidade
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, "listar", 0)
def list_handler():
    sel_disponibilidade = select(EquipamentoDisponibilidade)
    disponibilidade_paginada = SelectPagination(
        select=sel_disponibilidade, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['disponibilidades'] = disponibilidade_paginada.items
    g.extras['pagination'] = disponibilidade_paginada

@register_handler(dispatcher, "procurar", 0)
def search_prefetch():
    g.extras["equipamentos"] = get_equipamentos()

@register_handler(dispatcher, "procurar", 1)
def search_fetch():
    id_disponibilidade = none_if_empty(request.form.get('id_disponibilidade'), int)
    equipamento = none_if_empty(request.form.get('id_equipamento'), int)
    data_start = parse_date_string(request.form.get('data_start'))
    data_end = parse_date_string(request.form.get('data_end'))
    quantidade_min = none_if_empty(request.form.get('quantidade_min'), int)
    quantidade_max = none_if_empty(request.form.get('quantidade_max'), int)

    filters = []
    query_params = get_query_params(request)
    if id_disponibilidade is not None:
        filters.append(EquipamentoDisponibilidade.id_disponibilidade == id_disponibilidade)
    if equipamento is not None:
        filters.append(EquipamentoDisponibilidade.id_equipamento == equipamento)
    if data_start:
        filters.append(EquipamentoDisponibilidade.data >= data_start)
    if data_end:
        filters.append(EquipamentoDisponibilidade.data <= data_end)
    if quantidade_min:
        filters.append(EquipamentoDisponibilidade.quantidade_total >= quantidade_min)
    if quantidade_max:
        filters.append(EquipamentoDisponibilidade.quantidade_total <= quantidade_max)
    if filters:
        sel_disponibilidade = select(EquipamentoDisponibilidade).where(
            *filters
        )
        disponibilidade_paginada = SelectPagination(
            select=sel_disponibilidade, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['disponibilidades'] = disponibilidade_paginada.items
        g.extras['pagination'] = disponibilidade_paginada
        g.extras['query_params'] = query_params
    else:
        flash("especifique ao menos um campo", "danger")
        g.redirect_action, g.bloco = register_return(
            g.url, g.acao, g.extras,
            equipamentos = get_equipamentos()
        )