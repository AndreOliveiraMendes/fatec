from flask import g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_datetime_string
from app.dao.internal.reservas import get_reservas_auditorios_database
from app.decorators.decorators import register_handler
from app.enums import StatusEmailEnum
from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Email
from app.routes_helper.db_actions import db_action
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_notificacoes = select(Reserva_Auditorio_Email)
    notificacoes_paginadas = SelectPagination(
        select=sel_notificacoes, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['notificacoes'] = notificacoes_paginadas.items
    g.extras['pagination'] = notificacoes_paginadas

@register_handler(dispatcher, 'procurar', 0)
def search_prefeth():
    g.extras['reservas_auditorios'] = get_reservas_auditorios_database()

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['reservas_auditorios'] = get_reservas_auditorios_database()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_reserva_auditorio = get_value_or_abort(request.form.get('id_reserva_auditorio'), 400, "id_reserva_auditorio é obrigatorio", int)
    destinatario = get_value_or_abort(request.form.get('destinatario'), 400, "destinatário é obrigatorio")
    assunto = get_value_or_abort(request.form.get('assunto'), 400, "assunto é obrigatorio")
    corpo_email = get_value_or_abort(request.form.get('corpo_email'), 400, "conteudo é obrigatorio")
    status_envio = get_value_or_abort(request.form.get('status_envio'), 400, "status_envio é obrigatorio")
    data_envio = parse_datetime_string(request.form.get('data_envio'))
    erro_envio = none_if_empty(request.form.get('erro_envio'))
    tentativas = get_value_or_abort(request.form.get('tentativas'), 400, "tentativas é obrigatorio", int)
    ultima_tentativa = parse_datetime_string(request.form.get('ultima_tentativa'))

    nova_notificacao = Reserva_Auditorio_Email(
        id_reserva_auditorio = id_reserva_auditorio,
        destinatario = destinatario,
        assunto = assunto,
        corpo_email = corpo_email,
        status_envio = StatusEmailEnum(status_envio),
        data_envio = data_envio,
        erro_envio = erro_envio,
        tentativas = tentativas,
        ultima_tentativa = ultima_tentativa
    )
    
    db_action(
        "Inserção",
        "Notificação de reserva (auditorio/equipamentos) cadastrada com sucesso",
        "Erro ao cadastrar notificação (auditorio/equipamentos)",
        obj=nova_notificacao
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras
    )
