from datetime import datetime

from flask import g, request

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_datetime_string
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.usuarios import get_pessoas
from app.decorators.decorators import register_handler
from app.enums import TipoMovimentacaoEnum
from app.extensions import db
from app.models.controle import MovimentacaoEquipamento
from app.routes_helper.db_actions import db_action

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    pass

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    pass

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    pass

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

@register_handler(dispatcher, 'edit', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_movimentacoes():
    pass

@register_handler(dispatcher, 'edit', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_movimentacao():
    pass

@register_handler(dispatcher, 'edit', 2)
def edit_push():
    pass

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    pass