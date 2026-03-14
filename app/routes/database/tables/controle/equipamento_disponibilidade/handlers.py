from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string, parse_date_string_or_abort
from app.dao.internal.controle import get_equipamento_disponibilidades
from app.dao.internal.equipamentos import get_equipamentos
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.controle import EquipamentoDisponibilidade
from app.routes_helper.db_actions import db_action
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

@register_handler(dispatcher, "inserir", 0)
def insert_prefetch():
    g.extras["equipamentos"] = get_equipamentos()

@register_handler(dispatcher, "inserir", 1)
def insert_push():
    id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
    data = parse_date_string(request.form.get('data'))
    quantidade_total = none_if_empty(request.form.get('quantidade_total'), int)

    novo_registro_disponibilidade = EquipamentoDisponibilidade(
        id_equipamento=id_equipamento,
        data=data,
        quantidade_total=quantidade_total
    )

    def insert():
        db.session.add(novo_registro_disponibilidade)

    db_action(
        "Inserção",
        "Disponibilidade criada com sucesso",
        "Erro ao criar disponibilidade",
        obj=novo_registro_disponibilidade,
        action=insert
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        equipamentos=get_equipamentos()
    )

@register_handler(dispatcher, "editar", 0)
@register_handler(dispatcher, "excluir", 0)
def fetch_equipamentos_disponibilidades():
    g.extras['disponibilidades'] = get_equipamento_disponibilidades()

@register_handler(dispatcher, "editar", 1)
@register_handler(dispatcher, "excluir", 1)
def fetch_equipamento_disponibilidade():
    id_disponibilidade = none_if_empty(request.form.get('id_disponibilidade'), int)
    disponibilidade = db.get_or_404(EquipamentoDisponibilidade, id_disponibilidade)
    g.extras['disponibilidade'] = disponibilidade
    g.extras['equipamentos'] = get_equipamentos()

@register_handler(dispatcher, "editar", 2)
def edit_push():
    id_disponibilidade = none_if_empty(request.form.get('id_disponibilidade'), int)
    id_equipamento = get_value_or_abort(request.form.get('id_equipamento'), 400, 'id do equipamento é obrigatorio', int)
    data = parse_date_string_or_abort(request.form.get('data'), 400, 'data é obrigatoria')
    quantidade_total = get_value_or_abort(request.form.get('quantidade_total'), 400, 'a quantidade total é obrigatoria', int)

    disponibilidade = db.get_or_404(EquipamentoDisponibilidade, id_disponibilidade)
    dados_anteriores = copy(disponibilidade)

    def update():
        disponibilidade.id_equipamento = id_equipamento
        disponibilidade.data = data
        disponibilidade.quantidade_total = quantidade_total

    db_action(
        "Edição",
        "Disponibilidade editada com sucesso",
        "Erro ao editar disponilidade",
        obj=disponibilidade,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        disponibilidades=get_equipamento_disponibilidades()
    )

@register_handler(dispatcher, "excluir", 2)
def delete_push():
    id_disponibilidade = none_if_empty(request.form.get('id_disponibilidade'), int)

    disponibilidade = db.get_or_404(EquipamentoDisponibilidade, id_disponibilidade)

    def delete():
        db.session.delete(disponibilidade)

    db_action(
        "Exclusão",
        "Disponibilidade excluida com sucesso",
        "Erro ao excluir disponibilidade",
        obj=disponibilidade,
        action=delete
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        disponibilidades=get_equipamento_disponibilidades()
    )