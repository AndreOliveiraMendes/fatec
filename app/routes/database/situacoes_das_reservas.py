import copy

from flask import Blueprint, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_query_params,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          parse_date_string, register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_aulas_ativas, get_locais, get_situacoes
from app.auxiliar.decorators import admin_required
from app.models import (SituacaoChaveEnum, Situacoes_Das_Reserva,
                        TipoReservaEnum, db)
from config.general import PER_PAGE

bp = Blueprint('database_situacoes_das_reservas', __name__, url_prefix="/database")

@bp.route("/situacoes_das_reservas", methods=["GET", "POST"])
@admin_required
def gerenciar_situacoes_das_reservas():
    url = 'database_situacoes_das_reservas.gerenciar_situacoes_das_reservas'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {'url':url}
    if request.method == 'POST':
        if acao == 'listar':
            sel_situacoes = select(Situacoes_Das_Reserva)
            situacoes_das_reservas_paginadas = SelectPagination(
                select=sel_situacoes, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['situacoes_das_reservas'] = situacoes_das_reservas_paginadas.items
            extras['pagination'] = situacoes_das_reservas_paginadas

        elif acao == 'procurar' and bloco == 0:
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'procurar' and bloco == 1:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)
            id_situacao_local = none_if_empty(request.form.get('id_situacao_local'), int)
            id_situacao_aula = none_if_empty(request.form.get('id_situacao_aula'), int)
            situacao_dia = parse_date_string(request.form.get('situacao_dia'))
            situacao_chave = none_if_empty(request.form.get('situacao_chave'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
            filter = []
            query_params = get_query_params(request)
            if id_situacao is not None:
                filter.append(Situacoes_Das_Reserva.id_situacao == id_situacao)
            if id_situacao_local is not None:
                filter.append(Situacoes_Das_Reserva.id_situacao_local == id_situacao_local)
            if id_situacao_aula is not None:
                filter.append(Situacoes_Das_Reserva.id_situacao_aula == id_situacao_aula)
            if situacao_dia:
                filter.append(Situacoes_Das_Reserva.situacao_dia == situacao_dia)
            if situacao_chave:
                filter.append(Situacoes_Das_Reserva.situacao_chave == SituacaoChaveEnum(situacao_chave))
            if tipo_reserva:
                filter.append(Situacoes_Das_Reserva.tipo_reserva == TipoReservaEnum(tipo_reserva))
            if filter:
                sel_situacoes = select(Situacoes_Das_Reserva).where(*filter)
                situacoes_das_reservas_paginadas = SelectPagination(
                    select=sel_situacoes, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['situacoes_das_reservas'] = situacoes_das_reservas_paginadas.items
                extras['pagination'] = situacoes_das_reservas_paginadas
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
            id_situacao_local = none_if_empty(request.form.get('id_situacao_local'), int)
            id_situacao_aula = none_if_empty(request.form.get('id_situacao_aula'), int)
            situacao_dia = parse_date_string(request.form.get('situacao_dia'))
            situacao_chave = none_if_empty(request.form.get('situacao_chave'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            try:
                nova_situacao = Situacoes_Das_Reserva(
                    id_situacao_local = id_situacao_local,
                    id_situacao_aula = id_situacao_aula,
                    situacao_dia = situacao_dia,
                    situacao_chave = SituacaoChaveEnum(situacao_chave)
                )
                if tipo_reserva:
                    nova_situacao.tipo_reserva = TipoReservaEnum(tipo_reserva)
                db.session.add(nova_situacao)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_situacao)

                db.session.commit()
                flash("Situação cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar situação:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar situação:{ve}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras,
                locais=get_locais(), aulas_ativas=get_aulas_ativas()
            )

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['situacoes_das_reservas'] = get_situacoes()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)
            situacao_da_reserva = db.get_or_404(Situacoes_Das_Reserva, id_situacao)
            extras['situacao_da_reserva'] = situacao_da_reserva
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'editar' and bloco == 2:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)
            id_situacao_local = none_if_empty(request.form.get('id_situacao_local'), int)
            id_situacao_aula = none_if_empty(request.form.get('id_situacao_aula'), int)
            situacao_dia = parse_date_string(request.form.get('situacao_dia'))
            situacao_chave = none_if_empty(request.form.get('situacao_chave'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            situacao_da_reserva = db.get_or_404(Situacoes_Das_Reserva, id_situacao)
            try:
                dados_anteriores = copy.copy(situacao_da_reserva)
                situacao_da_reserva.id_situacao_local = id_situacao_local
                situacao_da_reserva.id_situacao_aula = id_situacao_aula
                situacao_da_reserva.situacao_dia = situacao_dia
                situacao_da_reserva.situacao_chave = SituacaoChaveEnum(situacao_chave)
                if tipo_reserva:
                    situacao_da_reserva.tipo_reserva = TipoReservaEnum(tipo_reserva)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', situacao_da_reserva, dados_anteriores)

                db.session.commit()
                flash("Situação Editada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao editar situação:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao editar situação:{ve}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras,
                situacoes_das_reservas=get_situacoes()
            )
        elif acao == 'excluir' and bloco == 2:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)

            situacao_da_reserva = db.get_or_404(Situacoes_Das_Reserva, id_situacao)
            try:
                db.session.delete(situacao_da_reserva)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', situacao_da_reserva)

                db.session.commit()
                flash("situação excluida com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir situação:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras,
                situacoes_das_reservas=get_situacoes()
            )
    if redirect_action:
        return redirect_action
    return render_template("database/table/situacoes_das_reservas.html",
        username=username, perm=perm, acao=acao, bloco=bloco, **extras)