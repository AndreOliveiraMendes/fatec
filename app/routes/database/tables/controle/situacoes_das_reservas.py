import copy

from flask import Blueprint, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string, parse_date_string_or_abort
from app.dao.internal.aulas import get_aulas_ativas
from app.dao.internal.controle import get_situacoes
from app.dao.internal.locais import get_locais
from app.decorators.decorators import admin_required, crud_route
from app.enums import SituacaoChaveEnum, TipoReservaEnum
from app.extensions import db
from app.models.controle import Situacoes_Das_Reserva
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

bp = Blueprint('database_situacoes_das_reservas', __name__, url_prefix="/database")

@bp.route("/situacoes_das_reservas", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_situacoes_das_reservas():
    if request.method == 'POST':
        if g.acao == 'listar':
            sel_situacoes = select(Situacoes_Das_Reserva)
            situacoes_das_reservas_paginadas = SelectPagination(
                select=sel_situacoes, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['situacoes_das_reservas'] = situacoes_das_reservas_paginadas.items
            g.extras['pagination'] = situacoes_das_reservas_paginadas

        elif g.acao == 'procurar' and g.bloco == 0:
            g.extras['locais'] = get_locais()
            g.extras['aulas_ativas'] = get_aulas_ativas()
        elif g.acao == 'procurar' and g.bloco == 1:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)
            id_situacao_local = none_if_empty(request.form.get('id_situacao_local'), int)
            id_situacao_aula = none_if_empty(request.form.get('id_situacao_aula'), int)
            situacao_dia = parse_date_string(request.form.get('situacao_dia'))
            situacao_chave = none_if_empty(request.form.get('situacao_chave'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
            filters = []
            query_params = get_query_params(request)
            if id_situacao is not None:
                filters.append(Situacoes_Das_Reserva.id_situacao == id_situacao)
            if id_situacao_local is not None:
                filters.append(Situacoes_Das_Reserva.id_situacao_local == id_situacao_local)
            if id_situacao_aula is not None:
                filters.append(Situacoes_Das_Reserva.id_situacao_aula == id_situacao_aula)
            if situacao_dia:
                filters.append(Situacoes_Das_Reserva.situacao_dia == situacao_dia)
            if situacao_chave:
                filters.append(Situacoes_Das_Reserva.situacao_chave == SituacaoChaveEnum(situacao_chave))
            if tipo_reserva:
                filters.append(Situacoes_Das_Reserva.tipo_reserva == TipoReservaEnum(tipo_reserva))
            if filters:
                sel_situacoes = select(Situacoes_Das_Reserva).where(*filters)
                situacoes_das_reservas_paginadas = SelectPagination(
                    select=sel_situacoes, session=db.session,
                    page=g.page, per_page=PER_PAGE, error_out=False
                )
                g.extras['situacoes_das_reservas'] = situacoes_das_reservas_paginadas.items
                g.extras['pagination'] = situacoes_das_reservas_paginadas
                g.extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo", "danger")
                g.redirect_action, g.bloco = register_return(
                    g.url, g.acao, g.extras,
                    locais=get_locais(), aulas_ativas=get_aulas_ativas()
                )

        elif g.acao == 'inserir' and g.bloco == 0:
            g.extras['locais'] = get_locais()
            g.extras['aulas_ativas'] = get_aulas_ativas()

        elif g.acao == 'inserir' and g.bloco == 1:
            id_situacao_local = none_if_empty(request.form.get('id_situacao_local'), int)
            id_situacao_aula = none_if_empty(request.form.get('id_situacao_aula'), int)
            situacao_dia = parse_date_string(request.form.get('situacao_dia'))
            situacao_chave = none_if_empty(request.form.get('situacao_chave'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            nova_situacao = Situacoes_Das_Reserva(
                id_situacao_local=id_situacao_local,
                id_situacao_aula=id_situacao_aula,
                situacao_dia=situacao_dia,
                situacao_chave=SituacaoChaveEnum(situacao_chave)
            )

            def insert():
                if tipo_reserva:
                    nova_situacao.tipo_reserva = TipoReservaEnum(tipo_reserva)

                db.session.add(nova_situacao)

            db_action(
                "Inserção",
                "Situação cadastrada com sucesso",
                "Erro ao cadastrar situação",
                obj=nova_situacao,
                action=insert
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                locais=get_locais(),
                aulas_ativas=get_aulas_ativas()
            )

        elif g.acao in ['editar', 'excluir'] and g.bloco == 0:
            g.extras['situacoes_das_reservas'] = get_situacoes()
        elif g.acao in ['editar', 'excluir'] and g.bloco == 1:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)
            situacao_da_reserva = db.get_or_404(Situacoes_Das_Reserva, id_situacao)
            g.extras['situacao_da_reserva'] = situacao_da_reserva
            g.extras['locais'] = get_locais()
            g.extras['aulas_ativas'] = get_aulas_ativas()

        elif g.acao == 'editar' and g.bloco == 2:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)
            id_situacao_local = get_value_or_abort(request.form.get('id_situacao_local'), 400, "id do local obrigatorio", int)
            id_situacao_aula = get_value_or_abort(request.form.get('id_situacao_aula'), 400, "id da aula é obrigatorio", int)
            situacao_dia = parse_date_string_or_abort(request.form.get('situacao_dia'), 400, "dia é obrigatorio")
            situacao_chave = none_if_empty(request.form.get('situacao_chave'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            situacao_da_reserva = db.get_or_404(Situacoes_Das_Reserva, id_situacao)
            dados_anteriores = copy.copy(situacao_da_reserva)

            def update():
                situacao_da_reserva.id_situacao_local = id_situacao_local
                situacao_da_reserva.id_situacao_aula = id_situacao_aula
                situacao_da_reserva.situacao_dia = situacao_dia
                situacao_da_reserva.situacao_chave = SituacaoChaveEnum(situacao_chave)

                if tipo_reserva:
                    situacao_da_reserva.tipo_reserva = TipoReservaEnum(tipo_reserva)

            db_action(
                "Edição",
                "Situação editada com sucesso",
                "Erro ao editar situação",
                obj=situacao_da_reserva,
                old_obj=dados_anteriores,
                action=update
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                situacoes_das_reservas=get_situacoes()
            )

        elif g.acao == 'excluir' and g.bloco == 2:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)

            situacao_da_reserva = db.get_or_404(Situacoes_Das_Reserva, id_situacao)

            def delete():
                db.session.delete(situacao_da_reserva)

            db_action(
                "Exclusão",
                "Situação excluida com sucesso",
                "Erro ao excluir situação",
                obj=situacao_da_reserva,
                action=delete
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                situacoes_das_reservas=get_situacoes()
            )

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/situacoes_das_reservas.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)