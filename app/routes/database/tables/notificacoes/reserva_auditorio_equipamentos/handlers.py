from flask import g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.reservas import get_reservas_auditorios_database
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Equipamentos
from app.routes_helper.db_actions import db_action
from config.general import PER_PAGE


dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_items = select(Reserva_Auditorio_Equipamentos)
    items_paginados = SelectPagination(
        select=sel_items, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['items'] = items_paginados.items
    g.extras['pagination'] = items_paginados
    
@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['reservas_auditorios'] = get_reservas_auditorios_database()
    g.extras['equipamentos'] = get_equipamentos()    

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['reservas_auditorios'] = get_reservas_auditorios_database()
    g.extras['equipamentos'] = get_equipamentos()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
    id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
    quantidade = none_if_empty(request.form.get('quantidade'))
    observacoes = none_if_empty(request.form.get('observacoes'))

    novo_item = Reserva_Auditorio_Equipamentos(
        id_reserva_auditorio = id_reserva_auditorio,
        id_equipamento = id_equipamento,
        quantidade = quantidade,
        observacoes = observacoes
    )

    db_action(
        'Inserção',
        'Relação inserida com sucesso',
        'Erro ao inserir relação',
        obj=novo_item
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        reservas_auditorios=get_reservas_auditorios_database(),
        equipamentos=get_equipamentos()
    )