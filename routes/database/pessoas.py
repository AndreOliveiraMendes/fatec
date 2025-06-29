import copy
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError
from main import app
from models import db, Pessoas, Usuarios
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import none_if_empty, get_query_params, get_user_info, registrar_log_generico

def get_pessoas_id_nome(acao, userid):
    pessoas_id_nome = db.session.query(Pessoas.id_pessoa, Pessoas.nome_pessoa)
    user = Usuarios.query.get(userid)
    if acao == 'excluir' and user:
        pessoas_id_nome = pessoas_id_nome.filter(Pessoas.id_pessoa!=user.id_pessoa)
    return pessoas_id_nome.all()

@app.route("/admin/pessoas", methods=["GET", "POST"])
@admin_required
def gerenciar_pessoas():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            pessoas_paginadas = Pessoas.query.paginate(page=page, per_page=10, error_out=False)
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
            query = Pessoas.query
            if id:
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
                pessoas_paginadas = query.filter(*filter).paginate(page=page, per_page=10, error_out=False)
                extras['pessoas'] = pessoas_paginadas.items
                extras['pagination'] = pessoas_paginadas
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                bloco = 0
        elif acao == 'inserir' and bloco == 1:
            nome = none_if_empty(request.form.get('nome', None))
            email = none_if_empty(request.form.get('email', None))
            try:
                nova_pessoa = Pessoas(nome_pessoa=nome, email_pessoa=email)
                db.session.add(nova_pessoa)
                db.session.flush()  # garante ID
                registrar_log_generico(userid, "Inserção", nova_pessoa)
                db.session.commit()
                flash("Pessoa cadastrada com sucesso", "success")
            except IntegrityError as e:
                flash(f"Erro ao inserir pessoa: {str(e.orig)}", "danger")
                db.session.rollback()
            bloco = 0
        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['pessoas'] = get_pessoas_id_nome(acao, userid)
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_pessoa = request.form.get('id_pessoa', None)
            pessoa = Pessoas.query.filter(Pessoas.id_pessoa == id_pessoa).first()
            if pessoa:
                extras['pessoa'] = pessoa
            else:
                flash("Pessoa não encontrada", "danger")
                extras['pessoas'] = get_pessoas_id_nome(acao, userid)
                bloco = 0
        elif acao == 'editar' and bloco == 2:
            id_pessoa = none_if_empty(request.form.get('id_pessoa'), int)
            nome = none_if_empty(request.form.get('nome', None))
            email = none_if_empty(request.form.get('email', None))

            pessoa = Pessoas.query.get(id_pessoa)

            if pessoa:
                try:
                    # Cria uma cópia dos dados antigos antes de editar
                    dados_anteriores = copy.copy(pessoa)

                    # Realiza as alterações
                    pessoa.nome_pessoa = nome
                    pessoa.email_pessoa = email

                    db.session.flush()  # Garante que o ID esteja atribuído

                    # Loga com os dados antigos + novos
                    registrar_log_generico(userid, "Edição", pessoa, dados_anteriores)

                    db.session.commit()
                    flash("Pessoa atualizada com sucesso", "success")

                except IntegrityError as e:
                    db.session.rollback()
                    flash(f"Erro ao atualizar pessoa: {str(e.orig)}", "danger")
            else:
                flash("Pessoa não encontrada", "danger")

            extras['pessoas'] = get_pessoas_id_nome(acao, userid)
            bloco = 0
        elif acao == 'excluir' and bloco == 2:
            user = Usuarios.query.get(userid)
            id_pessoa = none_if_empty(request.form.get('id_pessoa'), int)

            pessoa = Pessoas.query.get(id_pessoa)

            if pessoa:
                if user.id_pessoa == id_pessoa:
                    flash("Voce não pode se excluir", "danger")
                else:
                    try:
                        db.session.flush()  # garante ID
                        registrar_log_generico(userid, "Exclusão", pessoa)

                        db.session.delete(pessoa)
                        db.session.commit()
                        flash("Pessoa excluída com sucesso", "success")

                    except IntegrityError as e:
                        db.session.rollback()
                        flash(f"Erro ao excluir pessoa: {str(e.orig)}", "danger")
            else:
                flash("Pessoa não encontrada", "danger")

            extras['pessoas'] = get_pessoas_id_nome(acao, userid)
            bloco = 0

        return render_template("database/pessoas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/pessoas.html", username=username, perm=perm, acao=acao, bloco=bloco)