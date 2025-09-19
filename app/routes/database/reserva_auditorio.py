import copy

from flask import Blueprint, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import register_return, registrar_log_generico_usuario, get_session_or_request, get_user_info, none_if_empty, parse_date_string
from app.auxiliar.dao import get_aulas_ativas, get_locais, get_pessoas
from app.auxiliar.decorators import admin_required
from app.models import Reserva_Auditorio, StatusReservaAuditorioEnum, db
from config.general import PER_PAGE

bp = Blueprint('database_reserva_auditorio', __name__, url_prefix="/database")

@bp.route('/reserva_auditorio', methods=['GET', 'POST'])
@admin_required
def gerenciar_reserva_auditorio():
    url = 'database_reserva_auditorio.gerenciar_reserva_auditorio'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {'url':url}
    extras['SRAE'] = StatusReservaAuditorioEnum
    if request.method == 'POST':
        if acao == 'listar':
            sel_reservas = select(Reserva_Auditorio)
            reservas_auditorios_paginadas = SelectPagination(
                select=sel_reservas, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['reservas_auditorios'] = reservas_auditorios_paginadas.items
            extras['pagination'] = reservas_auditorios_paginadas

        elif acao == 'procurar':
            pass

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
                nova_reserva = Reserva_Auditorio(
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
    if redirect_action:
        return redirect_action
    return render_template("database/table/reserva_auditorio.html",
        username=username, perm=perm, acao=acao, bloco=bloco, **extras)