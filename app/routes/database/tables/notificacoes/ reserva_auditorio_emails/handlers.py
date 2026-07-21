from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_datetime_string
from app.dao.internal.notification import get_notificacoes_email
from app.dao.internal.reservas import get_reservas_auditorios_database
from app.decorators.decorators import register_handler
from app.enums import StatusEmailEnum
from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Email
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
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

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_email = none_if_empty(request.form.get('id_email'), int)
    id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
    destinatario = none_if_empty(request.form.get('destinatario'))
    assunto = none_if_empty(request.form.get('assunto'))
    corpo_email = none_if_empty(request.form.get('corpo_email'))
    status_envio = none_if_empty(request.form.get('status_envio'))
    data_envio = parse_datetime_string(request.form.get('data_envio'))
    erro_envio = none_if_empty(request.form.get('erro_envio'))
    tentativas = none_if_empty(request.form.get('tentativas'), int)
    ultima_tentativa = parse_datetime_string(request.form.get('ultima_tentativa'))

    filters = []
    query_params = get_query_params(request)
    if id_email is not None:
        filters.append(Reserva_Auditorio_Email.id_email == id_email)
    if id_reserva_auditorio is not None:
        filters.append(Reserva_Auditorio_Email.id_reserva_auditorio == id_reserva_auditorio)
    if destinatario:
        filters.append(Reserva_Auditorio_Email.destinatario.ilike(f"%{destinatario}%"))
    if assunto:
        filters.append(Reserva_Auditorio_Email.assunto.ilike(f"%{assunto}%"))
    if corpo_email:
        filters.append(Reserva_Auditorio_Email.corpo_email.ilike(f"%{corpo_email}%"))
    if status_envio:
        try:
            status_enum = StatusEmailEnum(status_envio)
        except ValueError:
            status_enum = None
        if status_enum is not None:
            filters.append(Reserva_Auditorio_Email.status_envio == status_enum)
    if data_envio:
        filters.append(Reserva_Auditorio_Email.data_envio == data_envio)
    if erro_envio:
        filters.append(Reserva_Auditorio_Email.erro_envio.ilike(f"%{erro_envio}%"))
    if tentativas is not None:
        filters.append(Reserva_Auditorio_Email.tentativas == tentativas)
    if ultima_tentativa:
        filters.append(Reserva_Auditorio_Email.ultima_tentativa == ultima_tentativa)
    if filters:
        sel_notificacoes = select(Reserva_Auditorio_Email).where(*filters)
        notificacoes_paginadas = SelectPagination(
            select=sel_notificacoes, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['notificacoes'] = notificacoes_paginadas.items
        g.extras['pagination'] = notificacoes_paginadas
        g.extras['query_params'] = query_params
    else:
        flash("especifique pelo menos um campo de busca", "danger")
        g.redirect_action, g.bloco = register_return(
            g.url, g.acao, g.extras,
            reservas_auditorios=get_reservas_auditorios_database()
        )

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
        g.url, g.acao, g.extras,
        reservas_auditorios=get_reservas_auditorios_database()
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_notificacoes():
    g.extras['notificacoes'] = get_notificacoes_email()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_notificao():
    id_email = none_if_empty(request.form.get('id_email'), int)
    notificacao = db.get_or_404(Reserva_Auditorio_Email, id_email)
    g.extras['notificacao'] = notificacao
    g.extras['reservas_auditorios'] = get_reservas_auditorios_database()

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_email = none_if_empty(request.form.get('id_email'), int)
    id_reserva_auditorio = get_value_or_abort(request.form.get('id_reserva_auditorio'), 400, "id_reserva_auditorio é obrigatorio", int)
    destinatario = get_value_or_abort(request.form.get('destinatario'), 400, "destinatário é obrigatorio")
    assunto = get_value_or_abort(request.form.get('assunto'), 400, "assunto é obrigatorio")
    corpo_email = get_value_or_abort(request.form.get('corpo_email'), 400, "conteudo é obrigatorio")
    status_envio = get_value_or_abort(request.form.get('status_envio'), 400, "status_envio é obrigatorio")
    data_envio = parse_datetime_string(request.form.get('data_envio'))
    erro_envio = none_if_empty(request.form.get('erro_envio'))
    tentativas = get_value_or_abort(request.form.get('tentativas'), 400, "tentativas é obrigatorio", int)
    ultima_tentativa = parse_datetime_string(request.form.get('ultima_tentativa'))

    notificacao = db.get_or_404(Reserva_Auditorio_Email, id_email)
    dados_anteriores = copy(notificacao)

    def update():
        notificacao.id_reserva_auditorio = id_reserva_auditorio
        notificacao.destinatario = destinatario
        notificacao.assunto = assunto
        notificacao.corpo_email = corpo_email
        notificacao.status_envio = StatusEmailEnum(status_envio)
        if data_envio:
            notificacao.data_envio = data_envio
        if erro_envio:
            notificacao.erro_envio = erro_envio
        notificacao.tentativas = tentativas
        if ultima_tentativa:
            notificacao.ultima_tentativa = ultima_tentativa

    db_action(
        "Edição",
        "Notificação editada com sucesso",
        "Erro ao editar notificacação",
        obj=notificacao,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        notificacoes = get_notificacoes_email()
    )

@register_handler(dispatcher, 'excluir', 2)
def delet_push():
    id_email = none_if_empty(request.form.get('id_email'), int)

    notificacao = db.get_or_404(Reserva_Auditorio_Email, id_email)

    db_action(
        "Exclusão",
        "Notificação excluida com sucesso",
        "Erro ao excluir notificação",
        notificacao
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        notificacoes = get_notificacoes_email()
    )   