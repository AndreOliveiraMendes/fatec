import copy

from flask import Blueprint, abort, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.usuarios import get_pessoas
from app.decorators.decorators import admin_required, crud_route
from app.extensions import db
from app.models.usuarios import Pessoas
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from app.routes_helper.ui import disable_action
from config.general import PER_PAGE

#from .handlers import dispatcher
#from .states import VALID_STATES

bp = Blueprint('database_pessoas', __name__, url_prefix="/database")

@bp.route("/pessoas", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_pessoas():
    disabled = ['inserir', 'excluir']
    disable_action(g.extras, disabled)
    if request.method == 'POST':
        if g.acao in disabled:
            abort(403, description="Esta funcionalidade está desabilitada no momento.")

        if g.acao == 'listar':
            sel_pessoas = select(Pessoas)
            pessoas_paginadas = SelectPagination(
                select=sel_pessoas, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['pessoas'] = pessoas_paginadas.items
            g.extras['pagination'] = pessoas_paginadas

        elif g.acao == 'procurar' and g.bloco == 1:
            id = none_if_empty(request.form.get('id_pessoa', None))
            nome = none_if_empty(request.form.get('nome', None))
            exact_name_match = 'emnome' in request.form
            alias = none_if_empty(request.form.get('alias', None))
            exact_alias_match = 'emalias' in request.form
            email = none_if_empty(request.form.get('email', None))
            exact_email_match = 'ememail' in request.form
            filters = []
            query_params = get_query_params(request)
            if id is not None:
                filters.append(Pessoas.id_pessoa == id)
            if nome:
                if exact_name_match:
                    filters.append(Pessoas.nome_pessoa == nome)
                else:
                    filters.append(Pessoas.nome_pessoa.ilike(f"%{nome}%"))
            if alias:
                if exact_alias_match:
                    filters.append(Pessoas.alias == alias)
                else:
                    filters.append(Pessoas.alias.ilike(f"%{alias}%"))
            if email:
                if exact_email_match:
                    filters.append(Pessoas.email_pessoa == email)
                else:
                    filters.append(Pessoas.email_pessoa.ilike(f"%{email}%"))
            if filters:
                sel_pessoas = select(Pessoas).where(*filters)
                pessoas_paginadas = SelectPagination(
                    select=sel_pessoas, session=db.session,
                    page=g.page, per_page=PER_PAGE, error_out=False
                )
                g.extras['pessoas'] = pessoas_paginadas.items
                g.extras['pagination'] = pessoas_paginadas
                g.extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras)

        elif g.acao == 'inserir' and g.bloco == 1:
            nome = none_if_empty(request.form.get('nome', None))
            alias = none_if_empty(request.form.get('alias', None))
            email = none_if_empty(request.form.get('email', None))

            nova_pessoa = Pessoas(
                nome_pessoa=nome,
                alias=alias,
                email_pessoa=email
            )

            def insert():
                db.session.add(nova_pessoa)

            db_action(
                "Inserção",
                "Pessoa cadastrada com sucesso",
                "Erro ao cadastrar pessoa",
                obj=nova_pessoa,
                action=insert
            )

            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras
            )

        elif g.acao in ['editar', 'excluir'] and g.bloco == 0:
            g.extras['pessoas'] = get_pessoas(g.acao, g.userid)
        elif g.acao in ['editar', 'excluir'] and g.bloco == 1:
            id_pessoa = request.form.get('id_pessoa', None)
            g.extras['pessoa'] = db.get_or_404(Pessoas, id_pessoa)

        elif g.acao == 'editar' and g.bloco == 2:
            id_pessoa = none_if_empty(request.form.get('id_pessoa'), int)
            nome = get_value_or_abort(request.form.get('nome', None), 400, "nome da pessoa é obrigatorio")
            alias = none_if_empty(request.form.get('alias', None))
            email = none_if_empty(request.form.get('email', None))

            pessoa = db.get_or_404(Pessoas, id_pessoa)
            dados_anteriores = copy.copy(pessoa)

            def update():
                pessoa.nome_pessoa = nome
                pessoa.alias = alias
                pessoa.email_pessoa = email

            db_action(
                "Edição",
                "Pessoa atualizada com sucesso",
                "Erro ao editar pessoa",
                obj=pessoa,
                old_obj=dados_anteriores,
                action=update
            )

            g.redirect_action, g.bloco = register_return(
                g.url,
                g.acao,
                g.extras,
                pessoas=get_pessoas(g.acao, g.userid)
            )

        elif g.acao == 'excluir' and g.bloco == 2:
            id_pessoa = none_if_empty(request.form.get('id_pessoa'), int)

            pessoa = db.get_or_404(Pessoas, id_pessoa)

            if g.user and g.user.id_pessoa == id_pessoa:
                flash("Voce não pode se excluir", "danger")

            else:

                def delete():
                    db.session.delete(pessoa)

                db_action(
                    "Exclusão",
                    "Pessoa excluída com sucesso",
                    "Erro ao excluir pessoa",
                    obj=pessoa,
                    action=delete
                )

            g.redirect_action, g.bloco = register_return(
                g.url,
                g.acao,
                g.extras,
                pessoas=get_pessoas(g.acao, g.userid)
            )

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/pessoas.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)