import copy
from typing import Any

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_query_params,
                                          get_session_or_request, get_user,
                                          none_if_empty, parse_date_string,
                                          register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import (get_aulas_ativas, get_locais, get_pessoas,
                              get_reservas_auditorios_database)
from app.auxiliar.decorators import admin_required
from app.models import Reservas_Auditorios, StatusReservaAuditorioEnum, db
from config.general import PER_PAGE

bp = Blueprint('database_reservas_auditorios', __name__, url_prefix="/database")

@bp.route('/reservas_auditorios', methods=['GET', 'POST'])
@admin_required
def gerenciar_reservas_auditorios():
    url = 'database_reservas_auditorios.gerenciar_reservas_auditorios'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {'url':url}
    extras['SRAE'] = StatusReservaAuditorioEnum
    if request.method == 'POST':
        if acao == 'listar':
            sel_reservas = select(Reservas_Auditorios)
            reservas_auditorios_paginadas = SelectPagination(
                select=sel_reservas, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['reservas_auditorios'] = reservas_auditorios_paginadas.items
            extras['pagination'] = reservas_auditorios_paginadas

        elif acao == 'procurar' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'procurar' and bloco == 1:
            id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            dia_reserva = parse_date_string(request.form.get('dia_reserva'))
            status_reserva = none_if_empty(request.form.get('status_reserva'),)
            id_autorizador = none_if_empty(request.form.get('id_autorizador'), int)
            observação_responsavel = none_if_empty(request.form.get('observação_responsavel'))
            observação_autorizador = none_if_empty(request.form.get('observação_autorizador'))
            filter = []
            query_params = get_query_params(request)
            if id_reserva_auditorio is not None:
                filter.append(Reservas_Auditorios.id_reserva_auditorio == id_reserva_auditorio)
            if id_responsavel is not None:
                filter.append(Reservas_Auditorios.id_responsavel == id_responsavel)
            if id_reserva_local is not None:
                filter.append(Reservas_Auditorios.id_reserva_local == id_reserva_local)
            if id_reserva_aula is not None:
                filter.append(Reservas_Auditorios.id_reserva_aula == id_reserva_aula)
            if dia_reserva:
                filter.append(Reservas_Auditorios.dia_reserva == dia_reserva)
            if status_reserva:
                filter.append(Reservas_Auditorios.status_reserva == StatusReservaAuditorioEnum(status_reserva))
            if id_autorizador is not None:
                filter.append(Reservas_Auditorios.id_autorizador == id_autorizador)
            if observação_responsavel:
                filter.append(Reservas_Auditorios.observação_responsavel.ilike(f"%{observação_responsavel}%"))
            if observação_autorizador:
                filter.append(Reservas_Auditorios.observação_autorizador.ilike(f"%{observação_autorizador}"))
            if filter:
                sel_reservas = select(Reservas_Auditorios).where(*filter)
                reservas_auditorios_paginadas = SelectPagination(
                select=sel_reservas, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
                extras['reservas_auditorios'] = reservas_auditorios_paginadas.items
                extras['pagination'] = reservas_auditorios_paginadas
                extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo", "danger")
                redirect_action, bloco = register_return(url, acao, extras,
                    pessoas=get_pessoas(), locais=get_locais(), aulas_ativas=get_aulas_ativas()
            )

        elif acao == 'inserir' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'inserir' and bloco == 1:
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            dia_reserva = parse_date_string(request.form.get('dia_reserva'))
            status_reserva = none_if_empty(request.form.get('status_reserva'),)
            id_autorizador = none_if_empty(request.form.get('id_autorizador'), int)
            observação_responsavel = none_if_empty(request.form.get('observação_responsavel'))
            observação_autorizador = none_if_empty(request.form.get('observação_autorizador'))

            try:
                nova_reserva = Reservas_Auditorios(
                    id_responsavel=id_responsavel,
                    id_reserva_local=id_reserva_local,
                    id_reserva_aula=id_reserva_aula,
                    dia_reserva=dia_reserva,
                    status_reserva=StatusReservaAuditorioEnum(status_reserva),
                    id_autorizador=id_autorizador,
                    observação_responsavel=observação_responsavel,
                    observação_autorizador=observação_autorizador
                )
                db.session.add(nova_reserva)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_reserva)

                db.session.commit()
                flash("Reserva cadastrada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar reserva:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar reserva:{ve}", "danger")

            redirect_action, bloco = register_return(url, acao, extras,
                pessoas=get_pessoas(), locais=get_locais(), aulas_ativas=get_aulas_ativas())

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['reservas_auditorios'] = get_reservas_auditorios_database()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
            reserva_auditorio = db.get_or_404(Reservas_Auditorios, id_reserva_auditorio)
            extras['reserva_auditorio'] = reserva_auditorio
            extras['pessoas'] = get_pessoas()
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'editar' and bloco == 2:
            id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            dia_reserva = parse_date_string(request.form.get('dia_reserva'))
            status_reserva = none_if_empty(request.form.get('status_reserva'),)
            id_autorizador = none_if_empty(request.form.get('id_autorizador'), int)
            observação_responsavel = none_if_empty(request.form.get('observação_responsavel'))
            observação_autorizador = none_if_empty(request.form.get('observação_autorizador'))
            reserva_auditorio = db.get_or_404(Reservas_Auditorios, id_reserva_auditorio)
            
            if id_responsavel is None or id_reserva_local is None or id_reserva_aula is None or \
               dia_reserva is None or status_reserva is None:
                abort(400, description="Campos obrigatórios não foram preenchidos.")
            try:
                dados_anteriores = copy.copy(reserva_auditorio)
                reserva_auditorio.id_responsavel = id_responsavel
                reserva_auditorio.id_reserva_local = id_reserva_local
                reserva_auditorio.id_reserva_aula = id_reserva_aula
                reserva_auditorio.dia_reserva = dia_reserva
                reserva_auditorio.status_reserva = StatusReservaAuditorioEnum(status_reserva)
                reserva_auditorio.id_autorizador = id_autorizador
                reserva_auditorio.observação_responsavel = observação_responsavel
                reserva_auditorio.observação_autorizador = observação_autorizador

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', reserva_auditorio, dados_anteriores)

                db.session.commit()
                flash("Reserva editada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao editar reserva:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao editar reserva:{ve}")

            redirect_action, bloco = register_return(url, acao, extras,
                reservas_auditorios=get_reservas_auditorios_database())
        elif acao == 'excluir' and bloco == 2:
            id_reserva_auditorio = none_if_empty(request.form.get('id_reserva_auditorio'), int)
            reserva_auditorio = db.get_or_404(Reservas_Auditorios, id_reserva_auditorio)
            try:
                db.session.delete(reserva_auditorio)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', reserva_auditorio)

                db.session.commit()
                flash("Reserva excluida com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir reserva:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras,
                reservas_auditorios=get_reservas_auditorios_database())
    if redirect_action:
        return redirect_action
    return render_template("database/table/reservas_auditorios.html",
        user=user, acao=acao, bloco=bloco, **extras)