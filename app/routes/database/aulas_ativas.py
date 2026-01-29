import copy
from typing import Any

from flask import Blueprint, flash, render_template, request, session, abort
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_query_params,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          parse_date_string, register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import (check_aula_ativa, get_aulas, get_aulas_ativas,
                              get_dias_da_semana)
from app.auxiliar.decorators import admin_required
from app.models import Aulas_Ativas, TipoAulaEnum, db
from config.general import PER_PAGE

bp = Blueprint('database_aulas_ativas', __name__, url_prefix="/database")

def filtro_intervalo(inicio_procura, fim_procura):
    if inicio_procura and fim_procura:
        return or_(
            and_(
                Aulas_Ativas.inicio_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao >= inicio_procura,
                Aulas_Ativas.inicio_ativacao <= fim_procura
            ), and_(
                Aulas_Ativas.inicio_ativacao.is_(None),
                Aulas_Ativas.fim_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao >= inicio_procura
            ), and_(
                Aulas_Ativas.inicio_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao.is_(None),
                Aulas_Ativas.inicio_ativacao <= fim_procura
            ), and_(
                Aulas_Ativas.inicio_ativacao.is_(None),
                Aulas_Ativas.fim_ativacao.is_(None)
            )
        )
    elif inicio_procura:
        return or_(
            Aulas_Ativas.fim_ativacao >= inicio_procura,
            Aulas_Ativas.fim_ativacao.is_(None)
        )
    elif fim_procura:
        return or_(
            Aulas_Ativas.inicio_ativacao <= fim_procura,
            Aulas_Ativas.inicio_ativacao.is_(None)
        )
    else:
        raise ValueError("Especifique ao menos um valor")

@bp.route("/aulas_ativas", methods=["GET", "POST"])
@admin_required
def gerenciar_aulas_ativas():
    url = 'database_aulas_ativas.gerenciar_aulas_ativas'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user_info(userid)
    extras: dict[str, Any] = {'url':url}
    if request.method == 'POST':
        if acao == 'listar':
            sel_aulas_ativas = select(Aulas_Ativas)
            aulas_ativas_paginadas = SelectPagination(
                select=sel_aulas_ativas, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['aulas_ativas'] = aulas_ativas_paginadas.items
            extras['pagination'] = aulas_ativas_paginadas

        elif acao == 'procurar' and bloco == 0:
            extras['aulas'] = get_aulas()
            extras['dias_da_semana'] = get_dias_da_semana()
        elif acao == 'procurar' and bloco == 1:
            id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            inicio_procura = parse_date_string(request.form.get('inicio_procura'))
            fim_procura = parse_date_string(request.form.get('fim_procura'))
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            tipo_aula = none_if_empty(request.form.get('tipo_aula'))
            filter = []
            query_params = get_query_params(request)
            if id_aula_ativa is not None:
                filter.append(Aulas_Ativas.id_aula_ativa == id_aula_ativa)
            if id_aula is not None:
                filter.append(Aulas_Ativas.id_aula == id_aula)
            if inicio_procura or fim_procura:
                filter.append(filtro_intervalo(inicio_procura, fim_procura))
            if id_semana is not None:
                filter.append(Aulas_Ativas.id_semana == id_semana)
            if tipo_aula:
                filter.append(Aulas_Ativas.tipo_aula == TipoAulaEnum(tipo_aula))
            if filter:
                sel_aulas_ativas = select(Aulas_Ativas).where(*filter)
                aulas_ativas_paginadas = SelectPagination(
                    select=sel_aulas_ativas, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['aulas_ativas'] = aulas_ativas_paginadas.items
                extras['pagination'] = aulas_ativas_paginadas
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(url, acao, extras,
                    aulas=get_aulas(), dias_da_semana=get_dias_da_semana())

        elif acao == 'inserir' and bloco == 0:
            extras['aulas'] = get_aulas()
            extras['dias_da_semana'] = get_dias_da_semana()
        elif acao == 'inserir' and bloco == 1:
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            inicio_ativacao = parse_date_string(request.form.get('inicio_ativacao'))
            fim_ativacao = parse_date_string(request.form.get('fim_ativacao'))
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            tipo_aula = none_if_empty(request.form.get('tipo_aula'))
            try:
                check_aula_ativa(inicio_ativacao, fim_ativacao, id_aula, id_semana, tipo_aula)
                nova_aula_ativa = Aulas_Ativas(
                    id_aula = id_aula, inicio_ativacao = inicio_ativacao, fim_ativacao = fim_ativacao,
                    id_semana = id_semana, tipo_aula = TipoAulaEnum(tipo_aula))
                db.session.add(nova_aula_ativa)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_aula_ativa)

                db.session.commit()
                flash("Aula ativa cadastrada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar aula ativa:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar:{str(ve)}", "danger")
            
            redirect_action, bloco = register_return(url, acao, extras,
                aulas=get_aulas(), dias_da_semana=get_dias_da_semana())

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
            aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)
            extras['aula_ativa'] = aula_ativa
            extras['aulas'] = get_aulas()
            extras['dias_da_semana'] = get_dias_da_semana()
        elif acao == 'editar' and bloco == 2:
            id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            inicio_ativacao = parse_date_string(request.form.get('inicio_ativacao'))
            fim_ativacao = parse_date_string(request.form.get('fim_ativacao'))
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            tipo_aula = none_if_empty(request.form.get('tipo_aula'))
            aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)
            if id_aula is None:
                abort(400, description="id_aula é obrigatório")
            if id_semana is None:
                abort(400, description="id_semana é obrigatório")
            try:
                check_aula_ativa(inicio_ativacao, fim_ativacao, id_aula, id_semana, tipo_aula, id_aula_ativa)
                dados_anteriores = copy.copy(aula_ativa)
                aula_ativa.id_aula = id_aula
                aula_ativa.inicio_ativacao = inicio_ativacao
                aula_ativa.fim_ativacao = fim_ativacao
                aula_ativa.id_semana = id_semana
                aula_ativa.tipo_aula = TipoAulaEnum(tipo_aula)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', aula_ativa, dados_anteriores)

                db.session.commit()
                flash("Aula ativa editada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao editar aula ativa:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar:{str(ve)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras,
                aulas_ativas=get_aulas_ativas())
        elif acao == 'excluir' and bloco == 2:
            id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
            aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)
            try:
                db.session.delete(aula_ativa)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', aula_ativa)

                db.session.commit()
                flash("Aula ativa excluida com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir aula ativa:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras,
                aulas_ativas=get_aulas_ativas())
    if redirect_action:
        return redirect_action
    return render_template("database/table/aulas_ativas.html",
        user=user, acao=acao, bloco=bloco, **extras)