from copy import copy

from flask import g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_time_string, parse_time_string_or_abort
from app.dao.internal.aulas import get_turnos
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.aulas import Turnos
from app.routes_helper.db_actions import db_action
from app.service.aulas_service import check_turno
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_situacoes = select(Turnos).order_by(Turnos.id_turno)
    turnos_paginados = SelectPagination(
        select=sel_situacoes, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['turnos'] = turnos_paginados.items
    g.extras['pagination'] = turnos_paginados

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    nome_turno = none_if_empty(request.form.get('nome_turno'))
    horario_inicio = parse_time_string(request.form.get('horario_inicio'))
    horario_fim = parse_time_string(request.form.get('horario_fim'))

    novo_turno = Turnos(
        nome_turno=nome_turno,
        horario_inicio=horario_inicio,
        horario_fim=horario_fim
    )

    def insert():
        check_turno(horario_inicio, horario_fim)
        db.session.add(novo_turno)

    db_action(
        "Inserção",
        "Turno cadastrado com sucesso",
        "Erro ao cadastrar turno",
        obj=novo_turno,
        action=insert
    )

    g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras)

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_turnos():
    g.extras['turnos'] = get_turnos()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_turno():
    id_turno = none_if_empty(request.form.get('id_turno'), int)
    turno = db.get_or_404(Turnos, id_turno)
    g.extras['turno'] = turno

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_turno = none_if_empty(request.form.get('id_turno'), int)
    nome_turno = get_value_or_abort(request.form.get('nome_turno'), 400, "nome de turno obrigatorio")
    horario_inicio = parse_time_string_or_abort(request.form.get('horario_inicio'), 400, "horario de inicio obrigatorio")
    horario_fim = parse_time_string_or_abort(request.form.get('horario_fim'), 400, "horario de fim obrigatorio")

    turno = db.get_or_404(Turnos, id_turno)
    dados_anteriores = copy(turno)

    def update():
        check_turno(horario_inicio, horario_fim, id_turno)

        turno.nome_turno = nome_turno
        turno.horario_inicio = horario_inicio
        turno.horario_fim = horario_fim

    db_action(
        "Edição",
        "Turno editado com sucesso",
        "Erro ao editar turno",
        obj=turno,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        turnos=get_turnos()
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_turno = none_if_empty(request.form.get('id_turno'), int)

    turno = db.get_or_404(Turnos, id_turno)

    def delete():
        db.session.delete(turno)

    db_action(
        "Exclusão",
        "Turno excluido com sucesso",
        "Erro ao excluir turno",
        obj=turno,
        action=delete
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        turnos=get_turnos()
    )
