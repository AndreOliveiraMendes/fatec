import copy

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (disable_action, get_query_params,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_pessoas
from app.auxiliar.decorators import admin_required
from app.models import Pessoas, Usuarios, db
from config.general import PER_PAGE

bp = Blueprint('database_pessoas', __name__, url_prefix="/database")

@bp.route("/pessoas", methods=["GET", "POST"])
@admin_required
def gerenciar_pessoas():
    url = 'database_pessoas.gerenciar_pessoas'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    disabled = ['inserir', 'editar', 'excluir']
    extras = {'url':url}
    disable_action(extras, disabled)
    if request.method == 'POST':
        if acao in disabled:
            abort(403, description="Esta funcionalidade está desabilitada no momento.")

        if acao == 'listar':
            sel_pessoas = select(Pessoas)
            pessoas_paginadas = SelectPagination(
                select=sel_pessoas, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['pessoas'] = pessoas_paginadas.items
            extras['pagination'] = pessoas_paginadas

        elif acao == 'procurar' and bloco == 1:
            id = none_if_empty(request.form.get('id_pessoa', None))
            nome = none_if_empty(request.form.get('nome', None))
            exact_name_match = 'emnome' in request.form
            email = none_if_empty(request.form.get('email', None))
            exact_email_match = 'ememail' in request.form
            filter = []
            query_params = get_query_params(request)
            if id is not None:
                filter.append(Pessoas.id_pessoa == id)
            if nome:
                if exact_name_match:
                    filter.append(Pessoas.nome_pessoa == nome)
                else:
                    filter.append(Pessoas.nome_pessoa.ilike(f"%{nome}%"))
            if email:
                if exact_email_match:
                    filter.append(Pessoas.email_pessoa == email)
                else:
                    filter.append(Pessoas.email_pessoa.ilike(f"%{email}%"))
            if filter:
                sel_pessoas = select(Pessoas).where(*filter)
                pessoas_paginadas = SelectPagination(
                    select=sel_pessoas, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['pessoas'] = pessoas_paginadas.items
                extras['pagination'] = pessoas_paginadas
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(url, acao, extras)

        elif acao == 'inserir' and bloco == 1:
            nome = none_if_empty(request.form.get('nome', None))
            email = none_if_empty(request.form.get('email', None))
            try:
                nova_pessoa = Pessoas(nome_pessoa=nome, email_pessoa=email)
                db.session.add(nova_pessoa)
                db.session.flush()  # garante ID
                registrar_log_generico_usuario(userid, "Inserção", nova_pessoa)
                db.session.commit()
                flash("Pessoa cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao inserir pessoa: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras)

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['pessoas'] = get_pessoas(acao, userid)
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_pessoa = request.form.get('id_pessoa', None)
            extras['pessoa'] = db.get_or_404(Pessoas, id_pessoa)
        elif acao == 'editar' and bloco == 2:
            id_pessoa = none_if_empty(request.form.get('id_pessoa'), int)
            nome = none_if_empty(request.form.get('nome', None))
            email = none_if_empty(request.form.get('email', None))

            pessoa = db.get_or_404(Pessoas, id_pessoa)

            try:
                # Cria uma cópia dos dados antigos antes de editar
                dados_anteriores = copy.copy(pessoa)

                # Realiza as alterações
                pessoa.nome_pessoa = nome
                pessoa.email_pessoa = email

                db.session.flush()  # Garante que o ID esteja atribuído

                # Loga com os dados antigos + novos
                registrar_log_generico_usuario(userid, "Edição", pessoa, dados_anteriores)

                db.session.commit()
                flash("Pessoa atualizada com sucesso", "success")

            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao atualizar pessoa: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, pessoas=get_pessoas(acao, userid))
        elif acao == 'excluir' and bloco == 2:
            user = db.session.get(Usuarios, userid)
            id_pessoa = none_if_empty(request.form.get('id_pessoa'), int)

            pessoa = db.get_or_404(Pessoas, id_pessoa)

            if user and user.id_pessoa == id_pessoa:
                flash("Voce não pode se excluir", "danger")
            else:
                try:
                    db.session.delete(pessoa)
                    
                    db.session.flush()  # garante ID
                    registrar_log_generico_usuario(userid, "Exclusão", pessoa)

                    db.session.commit()
                    flash("Pessoa excluída com sucesso", "success")

                except (IntegrityError, OperationalError) as e:
                    db.session.rollback()
                    flash(f"Erro ao excluir pessoa: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, pessoas=get_pessoas(acao, userid))
    if redirect_action:
        return redirect_action
    return render_template("database/table/pessoas.html",
        username=username, perm=perm, acao=acao, bloco=bloco, **extras)