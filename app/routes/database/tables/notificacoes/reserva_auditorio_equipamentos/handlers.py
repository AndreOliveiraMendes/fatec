from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.notification import get_notificacoes_equipamentos
from app.dao.internal.reservas import get_reservas_auditorios_database
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Equipamentos
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
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

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_item = none_if_empty(request.form.get('id_item'), int)
    id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
    id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
    quantidade = none_if_empty(request.form.get('quantidade'), int)
    observacoes = none_if_empty(request.form.get('observacoes'))

    filters = []
    query_params = get_query_params(request)
    if id_item is not None:
        filters.append(Reserva_Auditorio_Equipamentos.id_item == id_item)
    if id_reserva_auditorio is not None:
        filters.append(Reserva_Auditorio_Equipamentos.id_reserva_auditorio == id_reserva_auditorio)
    if id_equipamento is not None:
        filters.append(Reserva_Auditorio_Equipamentos.id_equipamento == id_equipamento)
    if quantidade is not None:
        filters.append(Reserva_Auditorio_Equipamentos.quantidade == quantidade)
    if observacoes:
        filters.append(Reserva_Auditorio_Equipamentos.observacoes.ilike(f"%{observacoes}%"))
    if filters:
        sel_items = select(Reserva_Auditorio_Equipamentos).where(*filters)
        items_paginados = SelectPagination(
            select=sel_items, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['items'] = items_paginados.items
        g.extras['pagination'] = items_paginados
        g.extras['query_params'] = query_params
    else:
        flash("especifique pelo menos um campo de busca", "danger")
        g.redirect_action, g.bloco = register_return(
            g.url, g.acao, g.extras,
            reservas_auditorios=get_reservas_auditorios_database(),
            equipamentos=get_equipamentos()
        )

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

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def item_fetch():
    g.extras['items'] = get_notificacoes_equipamentos()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def item_fetch():
    id_item = none_if_empty(request.form.get('id_item'), int)

    item = db.get_or_404(Reserva_Auditorio_Equipamentos, id_item)
    g.extras['item'] = item
    g.extras['reservas_auditorios'] = get_reservas_auditorios_database()
    g.extras['equipamentos'] = get_equipamentos()

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_item = none_if_empty(request.form.get('id_item'), int)
    id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
    id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
    quantidade = none_if_empty(request.form.get('quantidade'))
    observacoes = none_if_empty(request.form.get('observacoes'))

    item = db.get_or_404(Reserva_Auditorio_Equipamentos, id_item)
    dados_anteriores = copy(item)

    def update():
        item.reserva_auditorio = id_reserva_auditorio
        item.id_equipamento = id_equipamento
        item.quantidade = quantidade
        item.observacoes = observacoes

    db_action(
        'Edição',
        'Item editado com sucesso',
        'Erro ao editar item',
        obj=item,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        items = get_notificacoes_equipamentos()
    )

@register_handler(dispatcher, 'excluir', 2)
def delet_push():
    id_item = none_if_empty(request.form.get('id_item'), int)

    item = db.get_or_404(Reserva_Auditorio_Equipamentos, id_item)

    db_action(
        'Exclusão',
        'Item excluido com sucesso',
        'Erro ao excluir item',
        obj=item
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        items = get_notificacoes_equipamentos()
    )