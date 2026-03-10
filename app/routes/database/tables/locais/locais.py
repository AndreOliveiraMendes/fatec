import copy

from flask import Blueprint, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.locais import get_locais
from app.decorators.decorators import admin_required, crud_route
from app.enums import DisponibilidadeEnum, TipoLocalEnum
from app.extensions import db
from app.models.locais import Locais
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

bp = Blueprint('database_locais', __name__, url_prefix="/database")

@bp.route("/locais", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_locais():
    if request.method == 'POST':
        if g.acao == 'listar':
            sel_locais = select(Locais)
            locais_paginados = SelectPagination(
                select=sel_locais, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['locais'] = locais_paginados.items
            g.extras['pagination'] = locais_paginados

        elif g.acao == 'procurar' and g.bloco == 1:
            id_local = none_if_empty(request.form.get('id_local'), int)
            nome_local = none_if_empty(request.form.get('nome_local'))
            exact_name_match = 'emnome' in request.form
            descrição = none_if_empty(request.form.get('descrição'))
            disponibilidade = none_if_empty(request.form.get('disponibilidade'))
            tipo = none_if_empty(request.form.get('tipo'))
            filters = []
            query_params = get_query_params(request)
            if id_local is not None:
                filters.append(Locais.id_local == id_local)
            if nome_local:
                if exact_name_match:
                    filters.append(Locais.nome_local == nome_local)
                else:
                    filters.append(Locais.nome_local.ilike(f"%{nome_local}%"))
            if descrição:
                filters.append(Locais.descrição.ilike(f"%{descrição}%"))
            if disponibilidade:
                filters.append(Locais.disponibilidade == DisponibilidadeEnum(disponibilidade))
            if tipo:
                filters.append(Locais.tipo == TipoLocalEnum(tipo))
            if filters:
                sel_locais = select(Locais).where(*filters)
                locais_paginados = SelectPagination(
                    select=sel_locais, session=db.session,
                    page=g.page, per_page=PER_PAGE, error_out=False
                )
                g.extras['locais'] = locais_paginados.items
                g.extras['pagination'] = locais_paginados
                g.extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                g.redirect_action, g.bloco = register_return(
                    g.url, g.acao, g.extras
                )

        elif g.acao == 'inserir' and g.bloco == 1:
            nome_local = none_if_empty(request.form.get('nome_local'))
            descrição = none_if_empty(request.form.get('descrição'))
            disponibilidade = none_if_empty(request.form.get('disponibilidade'))
            tipo = none_if_empty(request.form.get('tipo'))
            try:
                novo_local = Locais(
                    nome_local=nome_local,
                    descrição=descrição,
                    disponibilidade=DisponibilidadeEnum(disponibilidade),
                    tipo=TipoLocalEnum(tipo)
                )
                db.session.add(novo_local)
                db.session.flush()
                registrar_log_generico_usuario(g.userid, "Inserção", novo_local)
                db.session.commit()
                flash("Local cadastrado com succeso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao cadastrar local")
            except ValueError as e:
                handle_db_error(e, "Erro ao cadastrar local")

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras
            )

        elif g.acao in ['editar', 'excluir'] and g.bloco == 0:
            g.extras['locais'] = get_locais()
        elif g.acao in ['editar', 'excluir'] and g.bloco == 1:
            id_local = none_if_empty(request.form.get('id_local'), int)
            local = db.get_or_404(Locais, id_local)
            g.extras['local'] = local
        elif g.acao == 'editar' and g.bloco == 2:
            id_local = none_if_empty(request.form.get('id_local'), int)
            nome_local = get_value_or_abort(request.form.get('nome_local'), 400, "nome do local é obrigatorio")
            descrição = none_if_empty(request.form.get('descrição'))
            disponibilidade = none_if_empty(request.form.get('disponibilidade'))
            tipo = none_if_empty(request.form.get('tipo'))

            local = db.get_or_404(Locais, id_local)
            try:
                dados_anteriores = copy.copy(local)

                local.nome_local = nome_local
                local.descrição = descrição
                local.disponibilidade = DisponibilidadeEnum(disponibilidade)
                local.tipo = TipoLocalEnum(tipo)

                db.session.flush()
                registrar_log_generico_usuario(g.userid, "Edição", local, dados_anteriores)

                db.session.commit()
                flash("local editado com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar local")
            except ValueError as e:
                handle_db_error(e, "Erro ao editar local")

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras, locais=get_locais()
            )
        elif g.acao == 'excluir' and g.bloco == 2:
            id_local = none_if_empty(request.form.get('id_local'), int)

            local = db.get_or_404(Locais, id_local)
            try:
                db.session.delete(local)

                db.session.flush()
                registrar_log_generico_usuario(g.userid, "Exclusão", local)

                db.session.commit()
                flash("local excluido com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao excluir local")

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras, locais=get_locais()
            )
    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/locais.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)