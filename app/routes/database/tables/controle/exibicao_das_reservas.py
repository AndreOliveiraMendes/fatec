import copy
from typing import Any

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import get_aulas_ativas
from app.dao.internal.controle import get_exibicoes
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.locais import get_locais
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.enums import TipoReservaEnum
from app.extensions import db
from app.models.controle import Exibicao_Reservas
from app.routes_helper.request import get_query_params, get_session_or_request
from config.database_views import get_url
from config.general import PER_PAGE

bp = Blueprint('database_exibicao_reservas', __name__, url_prefix="/database")

@bp.route("/exibicao_reservas", methods=["GET", "POST"])
@admin_required
def gerenciar_exibicao_reservas():
    url = get_url('database_exibicao_reservas')
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {'url':url}
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
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'procurar' and bloco == 1:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)
            id_exibicao_local = none_if_empty(request.form.get('id_exibicao_local'), int)
            id_exibicao_aula = none_if_empty(request.form.get('id_exibicao_aula'), int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
            filter = []
            query_params = get_query_params(request)
            if id_exibicao is not None:
                filter.append(Exibicao_Reservas.id_exibicao == id_exibicao)
            if id_exibicao_local is not None:
                filter.append(Exibicao_Reservas.id_exibicao_local == id_exibicao_local)
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
                    locais=get_locais(), aulas_ativas=get_aulas_ativas()
                )

        elif acao == 'inserir' and bloco == 0:
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'inserir' and bloco == 1:
            id_exibicao_local = none_if_empty(request.form.get('id_exibicao_local'), int)
            id_exibicao_aula = none_if_empty(request.form.get('id_exibicao_aula'), int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            try:
                nova_exibicao = Exibicao_Reservas(
                    id_exibicao_local = id_exibicao_local,
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
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao configurar exibicao")
            except ValueError as e:
                handle_db_error(e, "Erro ao configurar exibicao")

            redirect_action, bloco = register_return(
                url, acao, extras,
                locais=get_locais(), aulas_ativas=get_aulas_ativas()
            )

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['exibicao_reservas'] = get_exibicoes()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)
            exibicao_da_reserva = db.get_or_404(Exibicao_Reservas, id_exibicao)
            extras['exibicao_da_reserva'] = exibicao_da_reserva
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'editar' and bloco == 2:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)
            id_exibicao_local = none_if_empty(request.form.get('id_exibicao_local'), int)
            id_exibicao_aula = none_if_empty(request.form.get('id_exibicao_aula'), int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            exibicao_da_reserva = db.get_or_404(Exibicao_Reservas, id_exibicao)
            if id_exibicao_local is None or id_exibicao_aula is None or exibicao_dia is None:
                abort(400, description="Campos obrigatórios não preenchidos")
            try:
                dados_anteriores = copy.copy(exibicao_da_reserva)
                exibicao_da_reserva.id_exibicao_local = id_exibicao_local
                exibicao_da_reserva.id_exibicao_aula = id_exibicao_aula
                exibicao_dia = exibicao_dia
                if tipo_reserva:
                    exibicao_da_reserva.tipo_reserva = TipoReservaEnum(tipo_reserva)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', exibicao_da_reserva, dados_anteriores)

                db.session.commit()
                flash("Exibição atualizada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar exibicao")
            except ValueError as e:
                handle_db_error(e, "Erro ao editar exibicao")

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
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao excluir exibicao")

            redirect_action, bloco = register_return(
                url, acao, extras,
                exibicao_reservas = get_exibicoes()
            )
    if redirect_action:
        return redirect_action
    return render_template("database/table/exibicao_reservas.html", user=user, acao=acao, bloco=bloco, **extras)