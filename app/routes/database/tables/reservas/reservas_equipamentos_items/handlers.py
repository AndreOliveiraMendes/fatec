from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.reservas import get_reservas_equipamentos
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.reservas.reservas_equipamentos import Reserva_Equipamento_Item
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE


dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_items_reservas = select(Reserva_Equipamento_Item)
    items_paginados = SelectPagination(
        select=sel_items_reservas, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['items_reservas'] = items_paginados.items
    g.extras['pagination'] = items_paginados

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['reservas'] = get_reservas_equipamentos()
    g.extras['equipamentos'] = get_equipamentos()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_item = none_if_empty(request.form.get('id_item'), int)
    id_reserva = none_if_empty(request.form.get('id_reserva'), int)
    id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
    quantidade_min = none_if_empty(request.form.get('quantidade_min'), int)
    quantidade_max = none_if_empty(request.form.get('quantidade_max'), int)
    quantidade_devolvida_min = none_if_empty(request.form.get('quantidade_devolvida_min'), int)
    quantidade_devolvida_max = none_if_empty(request.form.get('quantidade_devolvida_max'), int)

    filters = []
    query_params = get_query_params(request)
    if id_item is not None:
        filters.append(Reserva_Equipamento_Item.id_item == id_item)
    if id_reserva is not None:
        filters.append(Reserva_Equipamento_Item.id_reserva == id_reserva)
    if id_equipamento is not None:
        filters.append(Reserva_Equipamento_Item.id_equipamento == id_equipamento)
    if quantidade_min is not None:
        filters.append(Reserva_Equipamento_Item.quantidade >= quantidade_min)
    if quantidade_max is not None:
        filters.append(Reserva_Equipamento_Item.quantidade <= quantidade_max)
    if quantidade_devolvida_min is not None:
        filters.append(Reserva_Equipamento_Item.devolvido >= quantidade_devolvida_min)
    if quantidade_devolvida_max is not None:
        filters.append(Reserva_Equipamento_Item.devolvido <= quantidade_devolvida_max)
    if filters:
        sel_items_reservas = select(Reserva_Equipamento_Item).where(
            *filters
        )
        items_paginados = SelectPagination(
            select=sel_items_reservas, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['items_reservas'] = items_paginados.items
        g.extras['pagination'] = items_paginados        
        g.extras['query_params'] = query_params
    else:
        flash("especifique ao menos um campo", "danger")
        g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
            reservas = get_reservas_equipamentos(), equipamentos = get_equipamentos()
    )

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['reservas'] = get_reservas_equipamentos()
    g.extras['equipamentos'] = get_equipamentos()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    pass

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_reservas_equipamentos_items():
    pass

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_reserva_equipamento_item():
    pass

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    pass

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    pass