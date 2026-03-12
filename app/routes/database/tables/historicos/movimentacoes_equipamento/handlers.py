import copy
from datetime import datetime, timedelta

from flask import current_app, flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string, parse_datetime_string
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.historicos import get_movimentacoes_equipamentos
from app.dao.internal.usuarios import get_pessoas
from app.decorators.decorators import register_handler
from app.enums import TipoMovimentacaoEnum
from app.extensions import db
from app.models.historicos import MovimentacaoEquipamento
from app.routes_helper.db_actions import db_action
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
    g.extras['pessoas'] = get_pessoas()

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
            equipamentos=get_equipamentos, pessoas=get_pessoas()
        )

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['equipamentos'] = get_equipamentos()
    g.extras['pessoas'] = get_pessoas()
    g.extras['now'] = datetime.now().strftime("%Y-%m-%dT%H:%M")

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
    tipo_movimentacao = none_if_empty(request.form.get('tipo_movimentacao'))
    quantidade = none_if_empty(request.form.get('quantidade'), int)
    data_registro = parse_datetime_string(request.form.get('data_registro'))
    id_funcionario = none_if_empty(request.form.get('id_funcionario'), int)
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    observacao = none_if_empty(request.form.get('observacao'))

    nova_movimentacao = MovimentacaoEquipamento(
        id_equipamento = id_equipamento,
        quantidade = quantidade,
        data_registro = data_registro,
        id_funcionario = id_funcionario,
        id_responsavel = id_responsavel,
        observacao = observacao
    )

    def insert():
        if tipo_movimentacao:
            nova_movimentacao.tipo = TipoMovimentacaoEnum(tipo_movimentacao)

        db.session.add(nova_movimentacao)
    
    db_action(
        "Inserção",
        "Movimentacao registrada com sucesso",
        "Erro ao registrar movimentacao",
        obj=nova_movimentacao,
        action=insert
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        equipamentos=get_equipamentos,
        pessoas=get_pessoas(),
        now=datetime.now().strftime("%Y-%m-%dT%H:%M")
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_movimentacoes():
    g.extras['movimentacoes'] = get_movimentacoes_equipamentos()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_movimentacao():
    id_movimentacao = none_if_empty(request.form.get('id_movimentacao'), int)

    movimentacao = db.get_or_404(MovimentacaoEquipamento, id_movimentacao)
    g.extras['movimentacao'] = movimentacao
    g.extras['equipamentos'] = get_equipamentos()
    g.extras['pessoas'] = get_pessoas()

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_movimentacao = none_if_empty(request.form.get('id_movimentacao'), int)
    id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
    tipo_movimentacao = none_if_empty(request.form.get('tipo_movimentacao'))
    quantidade = none_if_empty(request.form.get('quantidade'), int)
    data_registro = parse_datetime_string(request.form.get('data_registro'))
    id_funcionario = none_if_empty(request.form.get('id_funcionario'), int)
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    observacao = none_if_empty(request.form.get('observacao'))

    movimentacao = db.get_or_404(MovimentacaoEquipamento, id_movimentacao)

    dados_anteriores = copy.copy(movimentacao)

    def atualizar():
        movimentacao.id_equipamento = id_equipamento
        movimentacao.quantidade = quantidade
        if data_registro:
            movimentacao.data_registro = data_registro
        else:
            movimentacao.data_registro = datetime.now()
        movimentacao.id_funcionario = id_funcionario
        movimentacao.id_responsavel = id_responsavel
        movimentacao.observacao = observacao
        if tipo_movimentacao:
            movimentacao.tipo = TipoMovimentacaoEnum(tipo_movimentacao)

    db_action(
        "Edição",
        "Movimentação atualizada com sucesso",
        "Erro ao atualizar movimentação",
        obj=movimentacao,
        action=atualizar,
        old_obj=dados_anteriores
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        movimentacoes = get_movimentacoes_equipamentos()
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_movimentacao = none_if_empty(request.form.get('id_movimentacao'), int)

    movimentacao = db.get_or_404(MovimentacaoEquipamento, id_movimentacao)

    def delete():
        db.session.delete(movimentacao)

    db_action(
        "Exclusão",
        "Registro de movimentação excluida com sucesso",
        "Erro ao excluir registro de movimentação",
        obj=movimentacao,
        action=delete
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        movimentacoes = get_movimentacoes_equipamentos()
    )