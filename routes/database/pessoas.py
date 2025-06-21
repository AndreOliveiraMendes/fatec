import flask_sqlalchemy.session
from main import app
from flask import flash, session, render_template, request
from models import db, Pessoas
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import none_if_empty, get_query_params

@app.route("/admin/pessoas", methods=["GET", "POST"])
@admin_required
def gerenciar_pessoas():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    username = session.get('username', None)
    userid = session.get('userid')
    perm = 0
    if username:
        user_perm:Usuarios_Permissao = Usuarios_Permissao.query.filter_by(id_permissao_usuario=userid).first()
        if user_perm:
            perm = user_perm.permissao
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
            nova_pessoa = Pessoas(nome_pessoa=nome, email_pessoa=email)
            db.session.add(nova_pessoa)
            db.session.commit()
            flash("Pessoa cadastrada com sucesso", "success")
            bloco = 0
        elif acao in ['editar', 'excluir'] and bloco == 0:
            pessoas_id_nome = db.session.query(Pessoas.id_pessoa, Pessoas.nome_pessoa).all()
            extras['pessoas'] = pessoas_id_nome
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_pessoa = request.form.get('id_pessoa', None)
            pessoa = Pessoas.query.filter(Pessoas.id_pessoa == id_pessoa).first()
            extras['pessoa'] = pessoa
        elif acao == 'editar' and bloco == 2:
            id_pessoa = none_if_empty(request.form.get('id_pessoa'))
            nome = none_if_empty(request.form.get('nome', None))
            email = none_if_empty(request.form.get('email', None))

            pessoa = Pessoas.query.get(id_pessoa)

            if pessoa:
                pessoa.nome_pessoa = nome
                pessoa.email_pessoa = email
                db.session.commit()
                flash("Pessoa atualizada com sucesso", "success")
            else:
                flash("Pessoa não encontrada", "danger")

            pessoas_id_nome = db.session.query(Pessoas.id_pessoa, Pessoas.nome_pessoa).all()
            extras['pessoas'] = pessoas_id_nome
            bloco = 0
        elif acao == 'excluir' and bloco == 2:
            id_pessoa = none_if_empty(request.form.get('id_pessoa'))

            pessoa = Pessoas.query.get(id_pessoa)

            if pessoa:
                db.session.delete(pessoa)
                db.session.commit()
                flash("Pessoa excluída com sucesso", "success")
            else:
                flash("Pessoa não encontrada", "danger")

            pessoas_id_nome = db.session.query(Pessoas.id_pessoa, Pessoas.nome_pessoa).all()
            extras['pessoas'] = pessoas_id_nome
            bloco = 0

        return render_template("database/pessoas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/pessoas.html", username=username, perm=perm, acao=acao, bloco=bloco)