from flask import g, request

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.reservas import get_reservas_auditorios_database
from app.decorators.decorators import register_handler
from app.models.notifications import Reserva_Auditorio_Equipamentos
from app.routes_helper.db_actions import db_action


dispatcher = {}

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
        g.url, g.acao, g.extras
    )