import copy

from flask import Blueprint, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import and_, or_, select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import (get_aulas, get_aulas_ativas,
                                    get_dias_da_semana)
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.decorators.decorators import admin_required, crud_route
from app.enums import TipoAulaEnum
from app.extensions import db
from app.models.aulas import Aulas_Ativas
from app.routes_helper.request import get_query_params
from app.service.aulas_service import check_aula_ativa
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
@crud_route()
def gerenciar_aulas_ativas():
    if request.method == 'POST':
        if g.acao == 'listar':
            sel_aulas_ativas = select(Aulas_Ativas)
            aulas_ativas_paginadas = SelectPagination(
                select=sel_aulas_ativas, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['aulas_ativas'] = aulas_ativas_paginadas.items
            g.extras['pagination'] = aulas_ativas_paginadas

        elif g.acao == 'procurar' and g.bloco == 0:
            g.extras['aulas'] = get_aulas()
            g.extras['dias_da_semana'] = get_dias_da_semana()
        elif g.acao == 'procurar' and g.bloco == 1:
            id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            inicio_procura = parse_date_string(request.form.get('inicio_procura'))
            fim_procura = parse_date_string(request.form.get('fim_procura'))
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            tipo_aula = none_if_empty(request.form.get('tipo_aula'))
            filters = []
            query_params = get_query_params(request)
            if id_aula_ativa is not None:
                filters.append(Aulas_Ativas.id_aula_ativa == id_aula_ativa)
            if id_aula is not None:
                filters.append(Aulas_Ativas.id_aula == id_aula)
            if inicio_procura or fim_procura:
                filters.append(filtro_intervalo(inicio_procura, fim_procura))
            if id_semana is not None:
                filters.append(Aulas_Ativas.id_semana == id_semana)
            if tipo_aula:
                filters.append(Aulas_Ativas.tipo_aula == TipoAulaEnum(tipo_aula))
            if filters:
                sel_aulas_ativas = select(Aulas_Ativas).where(*filters)
                aulas_ativas_paginadas = SelectPagination(
                    select=sel_aulas_ativas, session=db.session,
                    page=g.page, per_page=PER_PAGE, error_out=False
                )
                g.extras['aulas_ativas'] = aulas_ativas_paginadas.items
                g.extras['pagination'] = aulas_ativas_paginadas
                g.extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
                    aulas=get_aulas(), dias_da_semana=get_dias_da_semana())

        elif g.acao == 'inserir' and g.bloco == 0:
            g.extras['aulas'] = get_aulas()
            g.extras['dias_da_semana'] = get_dias_da_semana()
        elif g.acao == 'inserir' and g.bloco == 1:
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
                registrar_log_generico_usuario(g.userid, 'Inserção', nova_aula_ativa)

                db.session.commit()
                flash("Aula ativa cadastrada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao cadastrar aula ativa")
            except ValueError as e:
                handle_db_error(e, "Erro ao cadastrar aula ativa")
            
            g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
                aulas=get_aulas(), dias_da_semana=get_dias_da_semana())

        elif g.acao in ['editar', 'excluir'] and g.bloco == 0:
            g.extras['aulas_ativas'] = get_aulas_ativas()
        elif g.acao in ['editar', 'excluir'] and g.bloco == 1:
            id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
            aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)
            g.extras['aula_ativa'] = aula_ativa
            g.extras['aulas'] = get_aulas()
            g.extras['dias_da_semana'] = get_dias_da_semana()
        elif g.acao == 'editar' and g.bloco == 2:
            id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
            id_aula = get_value_or_abort(request.form.get('id_aula'), 400, "id_aula é obrigatório", int)
            inicio_ativacao = parse_date_string(request.form.get('inicio_ativacao'))
            fim_ativacao = parse_date_string(request.form.get('fim_ativacao'))
            id_semana = get_value_or_abort(request.form.get('id_semana'), 400, "id_semana é obrigatorio", int)
            tipo_aula = none_if_empty(request.form.get('tipo_aula'))
            aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)
            try:
                check_aula_ativa(inicio_ativacao, fim_ativacao, id_aula, id_semana, tipo_aula, id_aula_ativa)
                dados_anteriores = copy.copy(aula_ativa)
                aula_ativa.id_aula = id_aula
                aula_ativa.inicio_ativacao = inicio_ativacao
                aula_ativa.fim_ativacao = fim_ativacao
                aula_ativa.id_semana = id_semana
                aula_ativa.tipo_aula = TipoAulaEnum(tipo_aula)

                db.session.flush()
                registrar_log_generico_usuario(g.userid, 'Edição', aula_ativa, dados_anteriores)

                db.session.commit()
                flash("Aula ativa editada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar aula ativa")
            except ValueError as e:
                handle_db_error(e, "Erro ao editar aula ativa")

            g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
                aulas_ativas=get_aulas_ativas())
        elif g.acao == 'excluir' and g.bloco == 2:
            id_aula_ativa = none_if_empty(request.form.get('id_aula_ativa'), int)
            aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)
            try:
                db.session.delete(aula_ativa)

                db.session.flush()
                registrar_log_generico_usuario(g.userid, 'Exclusão', aula_ativa)

                db.session.commit()
                flash("Aula ativa excluida com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao excluir aula ativa")

            g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras,
                aulas_ativas=get_aulas_ativas())
    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/aulas_ativas.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)