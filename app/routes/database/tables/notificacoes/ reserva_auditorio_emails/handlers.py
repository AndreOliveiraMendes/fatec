from flask import g, request

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.parsing import parse_datetime_string
from app.dao.internal.reservas import get_reservas_auditorios_database
from app.decorators.decorators import register_handler

dispatcher = {}

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['reservas_auditorios'] = get_reservas_auditorios_database()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_reserva_auditorio = get_value_or_abort(request.form.get('id_reserva_auditorio'), 400, "id_reserva_auditorio é obrigatorio", int)
    destinatario = get_value_or_abort(request.form.get('destinatario'), 400, "destinatário é obrigatorio")
    assunto = get_value_or_abort(request.form.get('assunto'), 400, "assunto é obrigatorio")
    conteudo = get_value_or_abort(request.form.get('conteudo'), 400, "conteudo é obrigatorio")
    status_envio = get_value_or_abort(request.form.get('status_envio'), 400, "status_envio é obrigatorio")
    data_envio = parse_datetime_string(request.form.get('data_envio'))
    erro_envio = none_if_empty(request.form.get('erro_envio'))
    tentativas = get_value_or_abort(request.form.get('tentativas'), 400, "tentativas é obrigatorio", int)
    ultima_tentativa = parse_datetime_string(request.form.get('ultima_tentativa'))