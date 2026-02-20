import copy
from typing import Any

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.auxiliar_routes import (_handle_db_error, get_query_params,
                                          get_session_or_request, get_user,
                                          none_if_empty, register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.dao import get_locais
from app.auxiliar.decorators import admin_required
from app.models import DisponibilidadeEnum, Locais, TipoLocalEnum, db
from config.general import PER_PAGE

bp = Blueprint('database_locais', __name__, url_prefix="/database")

@bp.route("/locais", methods=["GET", "POST"])
@admin_required
def gerenciar_locais():
    url = 'database_locais.gerenciar_locais'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {'url':url}
    if request.method == 'POST':
        if acao == 'listar':
            sel_locais = select(Locais)
            locais_paginados = SelectPagination(
                select=sel_locais, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['locais'] = locais_paginados.items
            extras['pagination'] = locais_paginados

        elif acao == 'procurar' and bloco == 1:
            id_local = none_if_empty(request.form.get('id_local'), int)
            nome_local = none_if_empty(request.form.get('nome_local'))
            exact_name_match = 'emnome' in request.form
            descrição = none_if_empty(request.form.get('descrição'))
            disponibilidade = none_if_empty(request.form.get('disponibilidade'))
            tipo = none_if_empty(request.form.get('tipo'))
            filter = []
            query_params = get_query_params(request)
            if id_local is not None:
                filter.append(Locais.id_local == id_local)
            if nome_local:
                if exact_name_match:
                    filter.append(Locais.nome_local == nome_local)
                else:
                    filter.append(Locais.nome_local.ilike(f"%{nome_local}%"))
            if descrição:
                filter.append(Locais.descrição.ilike(f"%{descrição}%"))
            if disponibilidade:
                filter.append(Locais.disponibilidade == DisponibilidadeEnum(disponibilidade))
            if tipo:
                filter.append(Locais.tipo == TipoLocalEnum(tipo))
            if filter:
                sel_locais = select(Locais).where(*filter)
                locais_paginados = SelectPagination(
                    select=sel_locais, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['locais'] = locais_paginados.items
                extras['pagination'] = locais_paginados
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(
                    url, acao, extras
                )

        elif acao == 'inserir' and bloco == 1:
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
                registrar_log_generico_usuario(userid, "Inserção", novo_local)
                db.session.commit()
                flash("Local cadastrado com succeso", "success")
            except DB_ERRORS as e:
                _handle_db_error(e, "Erro ao cadastrar local")
            except ValueError as e:
                _handle_db_error(e, "Erro ao cadastrar local")

            redirect_action, bloco = register_return(
                url, acao, extras
            )

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['locais'] = get_locais()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_local = none_if_empty(request.form.get('id_local'), int)
            local = db.get_or_404(Locais, id_local)
            extras['local'] = local
        elif acao == 'editar' and bloco == 2:
            id_local = none_if_empty(request.form.get('id_local'), int)
            nome_local = none_if_empty(request.form.get('nome_local'))
            descrição = none_if_empty(request.form.get('descrição'))
            disponibilidade = none_if_empty(request.form.get('disponibilidade'))
            tipo = none_if_empty(request.form.get('tipo'))

            local = db.get_or_404(Locais, id_local)
            if nome_local is None:
                abort(400, description="Nome do local é obrigatório.")
            try:
                dados_anteriores = copy.copy(local)

                local.nome_local = nome_local
                local.descrição = descrição
                local.disponibilidade = DisponibilidadeEnum(disponibilidade)
                local.tipo = TipoLocalEnum(tipo)

                db.session.flush()
                registrar_log_generico_usuario(userid, "Edição", local, dados_anteriores)

                db.session.commit()
                flash("local editado com sucesso", "success")
            except DB_ERRORS as e:
                _handle_db_error(e, "Erro ao editar local")
            except ValueError as e:
                _handle_db_error(e, "Erro ao editar local")

            redirect_action, bloco = register_return(
                url, acao, extras, locais=get_locais()
            )
        elif acao == 'excluir' and bloco == 2:
            id_local = none_if_empty(request.form.get('id_local'), int)

            local = db.get_or_404(Locais, id_local)
            try:
                db.session.delete(local)

                db.session.flush()
                registrar_log_generico_usuario(userid, "Exclusão", local)

                db.session.commit()
                flash("local excluido com sucesso", "success")
            except DB_ERRORS as e:
                _handle_db_error(e, "Erro ao excluir local")

            redirect_action, bloco = register_return(
                url, acao, extras, locais=get_locais()
            )
    if redirect_action:
        return redirect_action
    return render_template("database/table/locais.html",
        user=user, acao=acao, bloco=bloco, **extras)