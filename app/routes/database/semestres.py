import copy

from flask import Blueprint, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_query_params,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          parse_date_string, register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_semestres
from app.auxiliar.decorators import admin_required
from app.models import Semestres, db
from config.general import PER_PAGE

bp = Blueprint('database_semestres', __name__, url_prefix="/database")

@bp.route("/semestres", methods=["GET", "POST"])
@admin_required
def gerenciar_semestres():
    url = 'database_semestres.gerenciar_semestres'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user_info(userid)
    extras = {'url':url}
    if request.method == 'POST':
        if acao == 'listar':
            sel_semestres = select(Semestres)
            semestres_paginados = SelectPagination(
                select=sel_semestres, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['semestres'] = semestres_paginados.items
            extras['pagination'] = semestres_paginados

        elif acao == 'procurar' and bloco == 1:
            id_semestre = none_if_empty(request.form.get('id_semestre'), int)
            nome_semestre = none_if_empty(request.form.get('nome_semestre'))
            emnome_semestre = 'emnome_semestre' in request.form
            data_inicio = parse_date_string(request.form.get('data_inicio'))
            data_fim = parse_date_string(request.form.get('data_fim'))
            data_inicio_reserva = parse_date_string(request.form.get('data_inicio_reserva'))
            data_fim_reserva = parse_date_string(request.form.get('data_fim_reserva'))
            dias_de_prioridade = none_if_empty(request.form.get('prioridade'), int)
            filter = []
            query_params = get_query_params(request)
            if id_semestre is not None:
                filter.append(Semestres.id_semestre == id_semestre)
            if nome_semestre:
                if emnome_semestre:
                    filter.append(Semestres.nome_semestre == nome_semestre)
                else:
                    filter.append(Semestres.nome_semestre.ilike(f"%{nome_semestre}%"))
            if data_inicio:
                filter.append(Semestres.data_inicio == data_inicio)
            if data_fim:
                filter.append(Semestres.data_fim == data_fim)
            if data_inicio_reserva:
                filter.append(Semestres.data_inicio_reserva == data_inicio_reserva)
            if data_fim_reserva:
                filter.append(Semestres.data_fim_reserva == data_fim_reserva)
            if dias_de_prioridade is not None:
                filter.append(Semestres.dias_de_prioridade == dias_de_prioridade)
            if filter:
                sel_semestres = select(Semestres).where(*filter)
                semestres_paginados = semestres_paginados = SelectPagination(
                    select=sel_semestres, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['semestres'] = semestres_paginados.items
                extras['pagination'] = semestres_paginados
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(url, acao, extras)

        elif acao == 'inserir' and bloco == 1:
            nome_semestre = none_if_empty(request.form.get('nome_semestre'))
            data_inicio = parse_date_string(request.form.get('data_inicio'))
            data_fim = parse_date_string(request.form.get('data_fim'))
            data_inicio_reserva = parse_date_string(request.form.get('data_inicio_reserva'))
            data_fim_reserva = parse_date_string(request.form.get('data_fim_reserva'))
            dias_de_prioridade = none_if_empty(request.form.get('prioridade'), int)
            try:
                novo_semestre = Semestres(
                    nome_semestre = nome_semestre,
                    data_inicio = data_inicio, data_fim = data_fim,
                    data_inicio_reserva = data_inicio_reserva, data_fim_reserva = data_fim_reserva,
                    dias_de_prioridade = dias_de_prioridade
                )
                db.session.add(novo_semestre)
                db.session.flush()
                registrar_log_generico_usuario(userid, "Inserção", novo_semestre)
                db.session.commit()
                flash("Semestre cadastrado com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar semestre:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras)

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['semestres'] = get_semestres()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_semestre = none_if_empty(request.form.get('id_semestre'), int)
            semestre = db.get_or_404(Semestres, id_semestre)
            extras['semestre'] = semestre
        elif acao == 'editar' and bloco == 2:
            id_semestre = none_if_empty(request.form.get('id_semestre'), int)
            nome_semestre = none_if_empty(request.form.get('nome_semestre'))
            data_inicio = parse_date_string(request.form.get('data_inicio'))
            data_fim = parse_date_string(request.form.get('data_fim'))
            data_inicio_reserva = parse_date_string(request.form.get('data_inicio_reserva'))
            data_fim_reserva = parse_date_string(request.form.get('data_fim_reserva'))
            dias_de_prioridade = none_if_empty(request.form.get('prioridade'), int)
            semestre = db.get_or_404(Semestres, id_semestre)
            try:
                dados_anteriores = copy.copy(semestre)
                semestre.nome_semestre = nome_semestre
                semestre.data_inicio = data_inicio
                semestre.data_fim = data_fim
                semestre.data_inicio_reserva = data_inicio_reserva
                semestre.data_fim_reserva = data_fim_reserva
                semestre.dias_de_prioridade = dias_de_prioridade

                db.session.flush()
                registrar_log_generico_usuario(userid, "Edição", semestre, dados_anteriores)

                db.session.commit()
                flash("Semestre editado com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao editar semestre:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, semestres=get_semestres())
        elif acao == 'excluir' and bloco == 2:
            id_semestre = none_if_empty(request.form.get('id_semestre'), int)

            semestre = db.get_or_404(Semestres, id_semestre)
            try:
                db.session.delete(semestre)

                db.session.flush()
                registrar_log_generico_usuario(userid, "Exclusão", semestre)

                db.session.commit()
                flash("Semestre excluido com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir semestre:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, semestres=get_semestres())
    if redirect_action:
        return redirect_action
    return render_template("database/table/semestres.html",
        username=user.username, perm=user.perm, acao=acao, bloco=bloco, **extras)