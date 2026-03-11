import copy

from flask import Blueprint, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import get_aulas_ativas
from app.dao.internal.controle import get_exibicoes
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.locais import get_locais
from app.decorators.decorators import admin_required, crud_route
from app.enums import TipoReservaEnum
from app.extensions import db
from app.models.controle import Exibicao_Reservas
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

#from .handlers import dispatcher
#from .states import VALID_STATES

bp = Blueprint('database_exibicao_reservas', __name__, url_prefix="/database")

@bp.route("/exibicao_reservas", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_exibicao_reservas():
    if request.method == 'POST':
        if g.acao == 'listar':
            sel_exibicao = select(Exibicao_Reservas)
            exibicao_reservas_paginadas = SelectPagination(
                select=sel_exibicao, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['exibicao_reservas'] = exibicao_reservas_paginadas.items
            g.extras['pagination'] = exibicao_reservas_paginadas

        elif g.acao == 'procurar' and g.bloco == 0:
            g.extras['locais'] = get_locais()
            g.extras['aulas_ativas'] = get_aulas_ativas()
        elif g.acao == 'procurar' and g.bloco == 1:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)
            id_exibicao_local = none_if_empty(request.form.get('id_exibicao_local'), int)
            id_exibicao_aula = none_if_empty(request.form.get('id_exibicao_aula'), int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
            filters = []
            query_params = get_query_params(request)
            if id_exibicao is not None:
                filters.append(Exibicao_Reservas.id_exibicao == id_exibicao)
            if id_exibicao_local is not None:
                filters.append(Exibicao_Reservas.id_exibicao_local == id_exibicao_local)
            if id_exibicao_aula is not None:
                filters.append(Exibicao_Reservas.id_exibicao_aula == id_exibicao_aula)
            if exibicao_dia:
                filters.append(Exibicao_Reservas.exibicao_dia == exibicao_dia)
            if tipo_reserva:
                filters.append(Exibicao_Reservas.tipo_reserva == TipoReservaEnum(tipo_reserva))
            if filters:
                sel_exibicao = select(Exibicao_Reservas).where(*filters)
                exibicao_reservas_paginadas = SelectPagination(
                    select=sel_exibicao, session=db.session,
                    page=g.page, per_page=PER_PAGE, error_out=False
                )
                g.extras['exibicao_reservas'] = exibicao_reservas_paginadas.items
                g.extras['pagination'] = exibicao_reservas_paginadas
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
            id_exibicao_local = none_if_empty(request.form.get('id_exibicao_local'), int)
            id_exibicao_aula = none_if_empty(request.form.get('id_exibicao_aula'), int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            nova_exibicao = Exibicao_Reservas(
                id_exibicao_local=id_exibicao_local,
                id_exibicao_aula=id_exibicao_aula,
                exibicao_dia=exibicao_dia
            )

            def insert():
                if tipo_reserva:
                    nova_exibicao.tipo_reserva = TipoReservaEnum(tipo_reserva)

                db.session.add(nova_exibicao)

            db_action(
                "Inserção",
                "Exibicao configurada com sucesso",
                "Erro ao configurar exibicao",
                obj=nova_exibicao,
                action=insert
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                locais=get_locais(),
                aulas_ativas=get_aulas_ativas()
            )

        elif g.acao in ['editar', 'excluir'] and g.bloco == 0:
            g.extras['exibicao_reservas'] = get_exibicoes()
        elif g.acao in ['editar', 'excluir'] and g.bloco == 1:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)
            exibicao_da_reserva = db.get_or_404(Exibicao_Reservas, id_exibicao)
            g.extras['exibicao_da_reserva'] = exibicao_da_reserva
            g.extras['locais'] = get_locais()
            g.extras['aulas_ativas'] = get_aulas_ativas()

        elif g.acao == 'editar' and g.bloco == 2:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)
            id_exibicao_local = get_value_or_abort(request.form.get('id_exibicao_local'), 400, "id do local obrigatorio", int)
            id_exibicao_aula = get_value_or_abort(request.form.get('id_exibicao_aula'), 400, "id da aula obritagorio", int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            exibicao_da_reserva = db.get_or_404(Exibicao_Reservas, id_exibicao)
            dados_anteriores = copy.copy(exibicao_da_reserva)

            def update():
                exibicao_da_reserva.id_exibicao_local = id_exibicao_local
                exibicao_da_reserva.id_exibicao_aula = id_exibicao_aula
                exibicao_da_reserva.exibicao_dia = exibicao_dia

                if tipo_reserva:
                    exibicao_da_reserva.tipo_reserva = TipoReservaEnum(tipo_reserva)

            db_action(
                "Edição",
                "Exibição atualizada com sucesso",
                "Erro ao editar exibicao",
                obj=exibicao_da_reserva,
                old_obj=dados_anteriores,
                action=update
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                exibicao_reservas=get_exibicoes()
            )

        elif g.acao == 'excluir' and g.bloco == 2:
            id_exibicao = none_if_empty(request.form.get('id_exibicao'), int)

            exibicao_da_reserva = db.get_or_404(Exibicao_Reservas, id_exibicao)

            def delete():
                db.session.delete(exibicao_da_reserva)

            db_action(
                "Exclusão",
                "Configuração de exibição excluida com sucesso",
                "Erro ao excluir exibicao",
                obj=exibicao_da_reserva,
                action=delete
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras,
                exibicao_reservas=get_exibicoes()
            )

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/exibicao_reservas.html", user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)