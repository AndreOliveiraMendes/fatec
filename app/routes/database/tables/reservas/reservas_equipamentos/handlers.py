from datetime import datetime

from flask import g, request

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import get_aulas_ativas
from app.dao.internal.usuarios import get_pessoas
from app.decorators.decorators import register_handler
from app.enums import StatusReservaEquipamentoEnum
from app.extensions import db
from app.models.reservas.reservas_equipamentos import Reservas_Equipamentos
from app.routes_helper.db_actions import db_action

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    pass

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['aulas_ativas'] = get_aulas_ativas()
    g.extras['pessoas'] = get_pessoas()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    pass

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
    estado = none_if_empty(request.form.get('estado'))

    nova_reserva = Reservas_Equipamentos(
        id_reserva_aula = id_reserva_aula,
        id_reserva_responsavel = id_reserva_responsavel,
        data_reserva = data_reserva
    )

    def inserir():
        nova_reserva.estado = StatusReservaEquipamentoEnum(estado)
        if cancelado_por_id:
            nova_reserva.cancelado_por_id = cancelado_por_id
            nova_reserva.cancelado_em = datetime.now()

        db.session.add(nova_reserva)

    db_action(
        "Inserção",
        "Reserva inserida com sucesso",
        "Erro ao inserir reserva",
        obj=nova_reserva,
        action=inserir
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
