import copy
from typing import Any

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (disable_action,
                                          get_session_or_request, get_user,
                                          none_if_empty, parse_time_string,
                                          register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_turnos
from app.auxiliar.decorators import admin_required
from app.models import Turnos, db
from config.general import PER_PAGE

bp = Blueprint('database_turnos', __name__, url_prefix="/database")

@bp.route("/turnos", methods=["GET", "POST"])
@admin_required
def gerenciar_turnos():
    url = 'database_turnos.gerenciar_turnos'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    disabled = ['procurar']
    extras: dict[str, Any] = {'url':url}
    disable_action(extras, disabled)
    if request.method == 'POST':
        if acao in disabled:
            abort(403, description="Esta funcionalidade não foi implementada.")

        if acao == 'listar':
            sel_situacoes = select(Turnos).order_by(Turnos.id_turno)
            turnos_paginados = SelectPagination(
                select=sel_situacoes, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['turnos'] = turnos_paginados.items
            extras['pagination'] = turnos_paginados

        elif acao == 'inserir' and bloco == 1:
            nome_turno = none_if_empty(request.form.get('nome_turno'))
            horario_inicio = parse_time_string(request.form.get('horario_inicio'))
            horario_fim = parse_time_string(request.form.get('horario_fim'))
            try:
                novo_turno = Turnos(
                    nome_turno = nome_turno, horario_inicio = horario_inicio, horario_fim = horario_fim)
                db.session.add(novo_turno)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', novo_turno)

                db.session.commit()
                flash("Turno cadastrado com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar turno:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras)

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['turnos'] = get_turnos()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_turno = none_if_empty(request.form.get('id_turno'), int)
            turno = db.get_or_404(Turnos, id_turno)
            extras['turno'] = turno
        elif acao == 'editar' and bloco == 2:
            id_turno = none_if_empty(request.form.get('id_turno'), int)
            nome_turno = none_if_empty(request.form.get('nome_turno'))
            horario_inicio = parse_time_string(request.form.get('horario_inicio'))
            horario_fim = parse_time_string(request.form.get('horario_fim'))
            turno = db.get_or_404(Turnos, id_turno)
            
            if nome_turno is None:
                abort(400, description="O nome do turno não pode ser vazio.")
            if horario_inicio is None or horario_fim is None:
                abort(400, description="O horário de início e fim devem ser válidos.")
            try:
                dados_anteriores = copy.copy(turno)
                turno.nome_turno = nome_turno
                turno.horario_inicio = horario_inicio
                turno.horario_fim = horario_fim
                db.session.flush
                registrar_log_generico_usuario(userid, 'Edição', turno, dados_anteriores)

                db.session.commit()
                flash("Turno editado com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao editar turno:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, turnos=get_turnos())
        elif acao == 'excluir' and bloco == 2:
            id_turno = none_if_empty(request.form.get('id_turno'), int)
            turno = db.get_or_404(Turnos, id_turno)
            try:
                db.session.delete(turno)
                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', turno)

                db.session.commit()
                flash("Turno excluido com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro as excluir turno", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, turnos=get_turnos())

    if redirect_action:
        return redirect_action
    return render_template("database/table/turnos.html",
        user=user, acao=acao, bloco=bloco, **extras)