from datetime import timedelta

from flask import current_app, flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.equipamentos import get_equipamentos
from app.decorators.decorators import register_handler
from app.enums import TipoMovimentacaoEnum
from app.extensions import db
from app.models.historicos import MovimentacaoEquipamento
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_movimentacoes = select(MovimentacaoEquipamento)
    movimentacoes_paginadas = SelectPagination(
        select=sel_movimentacoes, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['movimentacoes'] = movimentacoes_paginadas.items
    g.extras['pagination'] = movimentacoes_paginadas

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['equipamentos'] = get_equipamentos()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_movimentacao = none_if_empty(request.form.get("id_movimentacao"), int)
    id_equipamento = none_if_empty(request.form.get("id_equipamento"), int)
    tipo_movimentacao = none_if_empty(request.form.get("tipo_movimentacao"))
    quantidade = none_if_empty(request.form.get("quantidade"), int)
    data_inicio = parse_date_string(request.form.get("data_inicio"))
    data_fim = parse_date_string(request.form.get("data_fim"))
    id_funcionario = none_if_empty(request.form.get("id_funcionario"), int)
    id_responsavel = none_if_empty(request.form.get("id_responsavel"), int)
    observacao = none_if_empty(request.form.get("observacao"))
    filters = []
    query_params = get_query_params(request)
    if id_movimentacao is not None:
        filters.append(MovimentacaoEquipamento.id_movimentacao == id_movimentacao)
    if id_equipamento is not None:
        filters.append(MovimentacaoEquipamento.id_equipamento == id_equipamento)
    if tipo_movimentacao:
        try:
            tipo_enum = TipoMovimentacaoEnum(tipo_movimentacao)
        except ValueError:
            current_app.logger.warning(
                "tipo de movimentacao invalida: %s",
                tipo_movimentacao
            )
        else:
            filters.append(MovimentacaoEquipamento.tipo == tipo_enum)
    if quantidade is not None:
        filters.append(MovimentacaoEquipamento.quantidade == quantidade)
    if data_inicio:
        filters.append(MovimentacaoEquipamento.data_registro >= data_inicio)
    if data_fim:
        data_fim += timedelta(days=1)
        filters.append(MovimentacaoEquipamento.data_registro < data_fim)
    if id_funcionario is not None:
        filters.append(MovimentacaoEquipamento.id_funcionario == id_funcionario)
    if id_responsavel is not None:
        filters.append(MovimentacaoEquipamento.id_responsavel == id_responsavel)
    if observacao:
        filters.append(MovimentacaoEquipamento.observacao.ilike(f"%{observacao}%"))
    if filters:
        sel_movimentacoes = select(MovimentacaoEquipamento).where(
            *filters
        )
        movimentacoes_paginadas = SelectPagination(
            select=sel_movimentacoes, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['movimentacoes'] = movimentacoes_paginadas.items
        g.extras['pagination'] = movimentacoes_paginadas
        g.extras['query_params'] = query_params
    else:
        flash("especifique ao menos um campo", "danger")
        g.redirect_action, g.bloco = register_return(
            g.url, g.acao, g.extras,
            equipamentos=get_equipamentos
        )