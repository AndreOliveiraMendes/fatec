import copy
from typing import Any

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_query_params,
                                          get_session_or_request, get_user,
                                          none_if_empty, parse_time_string,
                                          register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_aulas
from app.auxiliar.decorators import admin_required
from app.models import Aulas, db
from config.general import PER_PAGE

bp = Blueprint('database_aulas', __name__, url_prefix="/database")

@bp.route("/aulas", methods=["GET", "POST"])
@admin_required
def gerenciar_aulas():
    url = 'database_aulas.gerenciar_aulas'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {'url':url}
    if request.method == 'POST':
        if acao == 'listar':
            sel_aulas = select(Aulas)
            aulas_paginadas = SelectPagination(
                select=sel_aulas, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['aulas'] = aulas_paginadas.items
            extras['pagination'] = aulas_paginadas

        elif acao == 'procurar' and bloco == 1:
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            horario_inicio_start = parse_time_string(request.form.get('horario_inicio_start'))
            horario_inicio_end = parse_time_string(request.form.get('horario_inicio_end'))
            horario_fim_start = parse_time_string(request.form.get('horario_fim_start'))
            horario_fim_end = parse_time_string(request.form.get('horario_fim_end'))
            filter = []
            query_params = get_query_params(request)
            if id_aula is not None:
                filter.append(Aulas.id_aula == id_aula)
            if horario_inicio_start or horario_inicio_end:
                if horario_inicio_start and horario_inicio_end:
                    filter.append(Aulas.horario_inicio.between(horario_inicio_start, horario_inicio_end))
                elif horario_inicio_start:
                    filter.append(Aulas.horario_inicio >= horario_inicio_start)
                else:
                    filter.append(Aulas.horario_inicio <= horario_inicio_end)
            if horario_fim_start or horario_fim_end:
                if horario_fim_start and horario_fim_end:
                    filter.append(Aulas.horario_fim.between(horario_fim_start, horario_fim_end))
                elif horario_fim_start:
                    filter.append(Aulas.horario_fim >= horario_fim_start)
                else:
                    filter.append(Aulas.horario_fim <= horario_fim_end)
            if filter:
                sel_aulas = select(Aulas).where(*filter)
                aulas_paginadas = SelectPagination(
                    select=sel_aulas, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['aulas'] = aulas_paginadas.items
                extras['pagination'] = aulas_paginadas
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(url, acao, extras)

        elif acao == 'inserir' and bloco == 1:
            horario_inicio = parse_time_string(request.form.get('horario_inicio'))
            horario_fim = parse_time_string(request.form.get('horario_fim'))
            try:
                nova_aula = Aulas(horario_inicio=horario_inicio, horario_fim=horario_fim)
                db.session.add(nova_aula)
                db.session.flush()
                registrar_log_generico_usuario(userid, "Inserção", nova_aula)
                db.session.commit()
                flash("Aula cadastrada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar aula: {str(e.orig)}", "danger")
            redirect_action, bloco = register_return(url, acao, extras)

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['aulas'] = get_aulas()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            aula = db.get_or_404(Aulas, id_aula)
            extras['aula'] = aula
        elif acao == 'editar' and bloco == 2:
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            horario_inicio = parse_time_string(request.form.get('horario_inicio'))
            horario_fim = parse_time_string(request.form.get('horario_fim'))
            aula = db.get_or_404(Aulas, id_aula)
            if horario_inicio is None or horario_fim is None:
                abort(400, description="Horário de início e fim são obrigatórios.")
            try:
                dados_anteriores = copy.copy(aula)
                aula.horario_inicio = horario_inicio
                aula.horario_fim = horario_fim

                db.session.flush()
                registrar_log_generico_usuario(userid, "Edição", aula, dados_anteriores)

                db.session.commit()
                flash("Aula editada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao editar aula: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras, aulas=get_aulas())
        elif acao == 'excluir' and bloco == 2:
            id_aula = none_if_empty(request.form.get('id_aula'), int)

            aula = db.get_or_404(Aulas, id_aula)
            try:
                db.session.delete(aula)

                db.session.flush()
                registrar_log_generico_usuario(userid, "Exclusão", aula)

                db.session.commit()
                flash("Aula excluida com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir aula: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras, aulas=get_aulas())
    if redirect_action:
        return redirect_action
    return render_template("database/table/aulas.html", user=user, acao=acao, bloco=bloco, **extras)