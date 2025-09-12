import copy

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_query_params,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          parse_date_string, register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_aulas_ativas, get_exibicoes, get_laboratorios
from app.auxiliar.decorators import admin_required
from app.models import Exibicao_Reservas, TipoReservaEnum, db
from config.general import PER_PAGE

bp = Blueprint('database_exibicao_reservas', __name__, url_prefix="/database")

@bp.route("/exibicao_reservas", methods=["GET", "POST"])
@admin_required
def gerenciar_exibicao_reservas():
    url = 'database_exibicao_reservas.gerenciar_exibicao_reservas'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {'url':url}
    if request.method == 'POST':
        if acao == 'listar':
            sel_exibicao = select(Exibicao_Reservas)
            exibicao_reservas_paginadas = SelectPagination(
                select=sel_exibicao, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['exibicao_reservas'] = exibicao_reservas_paginadas.items
            extras['pagination'] = exibicao_reservas_paginadas

        elif acao == 'procurar' and bloco == 0:
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'procurar' and bloco == 1:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)
            id_exibicao_laboratorio = none_if_empty(request.form.get('id_exibicao_laboratorio'), int)
            id_exibicao_aula = none_if_empty(request.form.get('id_exibicao_aula'), int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
            filter = []
            query_params = get_query_params(request)
            if id_exibicao is not None:
                filter.append(Exibicao_Reservas.id_exibicao == id_exibicao)
            if id_exibicao_laboratorio is not None:
                filter.append(Exibicao_Reservas.id_exibicao_laboratorio == id_exibicao_laboratorio)
            if id_exibicao_aula is not None:
                filter.append(Exibicao_Reservas.id_exibicao_aula == id_exibicao_aula)
            if exibicao_dia:
                filter.append(Exibicao_Reservas.exibicao_dia == exibicao_dia)
            if tipo_reserva:
                filter.append(Exibicao_Reservas.tipo_reserva == TipoReservaEnum(tipo_reserva))
            if filter:
                sel_exibicao = select(Exibicao_Reservas).where(*filter)
                exibicao_reservas_paginadas = SelectPagination(
                    select=sel_exibicao, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['exibicao_reservas'] = exibicao_reservas_paginadas.items
                extras['pagination'] = exibicao_reservas_paginadas
                extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo", "danger")
                redirect_action, bloco = register_return(
                    url, acao, extras,
                    laboratorios=get_laboratorios(), aulas_ativas=get_aulas_ativas()
                )

        elif acao == 'inserir' and bloco == 0:
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'inserir' and bloco == 1:
            id_exibicao_laboratorio = none_if_empty(request.form.get('id_exibicao_laboratorio'), int)
            id_exibicao_aula = none_if_empty(request.form.get('id_exibicao_aula'), int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            try:
                nova_exibicao = Exibicao_Reservas(
                    id_exibicao_laboratorio = id_exibicao_laboratorio,
                    id_exibicao_aula = id_exibicao_aula,
                    exibicao_dia = exibicao_dia
                )
                if tipo_reserva:
                    nova_exibicao.tipo_reserva = TipoReservaEnum(tipo_reserva)
                db.session.add(nova_exibicao)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_exibicao)

                db.session.commit()
                flash("Exibicao configurada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao configurar exibicao:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao configurar exibicao:{ve}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras,
                laboratorios=get_laboratorios(), aulas_ativas=get_aulas_ativas()
            )

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['exibicao_reservas'] = get_exibicoes()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)
            exibicao_da_reserva = db.get_or_404(Exibicao_Reservas, id_exibicao)
            extras['exibicao_da_reserva'] = exibicao_da_reserva
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'editar' and bloco == 2:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)
            id_exibicao_laboratorio = none_if_empty(request.form.get('id_exibicao_laboratorio'), int)
            id_exibicao_aula = none_if_empty(request.form.get('id_exibicao_aula'), int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            exibicao_da_reserva = db.get_or_404(Exibicao_Reservas, id_exibicao)
            try:
                dados_anteriores = copy.copy(exibicao_da_reserva)
                exibicao_da_reserva.id_exibicao_laboratorio = id_exibicao_laboratorio
                exibicao_da_reserva.id_exibicao_aula = id_exibicao_aula
                exibicao_dia = exibicao_dia
                if tipo_reserva:
                    exibicao_da_reserva.tipo_reserva = TipoReservaEnum(tipo_reserva)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', exibicao_da_reserva, dados_anteriores)

                db.session.commit()
                flash("Exibição atualizada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao editar exibição:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao editar exibição:{ve}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras,
                exibicao_reservas = get_exibicoes()
            )

        elif acao == 'excluir' and bloco == 2:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)

            exibicao_da_reserva = db.get_or_404(Exibicao_Reservas, id_exibicao)
            try:
                db.session.delete(exibicao_da_reserva)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', exibicao_da_reserva)

                db.session.commit()
                flash("Configuração de exibição excluida com sucessor", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir configuração de exibição:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras,
                exibicao_reservas = get_exibicoes()
            )
    if redirect_action:
        return redirect_action
    return render_template("database/table/exibicao_reservas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)