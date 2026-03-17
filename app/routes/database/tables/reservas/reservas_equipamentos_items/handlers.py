from flask import g
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.reservas import get_reservas_equipamentos
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.reservas.reservas_equipamentos import Reserva_Equipamento_Item
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
    pass

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    pass

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