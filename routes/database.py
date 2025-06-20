from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Reservas_Fixa, Usuarios, Pessoas, Usuarios_Permissao, Laboratorios, Aulas
from decorators import admin_required

IGNORED_FORM_FIELDS = ['page', 'acao', 'bloco']

def none_if_empty(value):
    return value if value and value.strip() else None

def get_query_params(request):
    return {key: value for key, value in request.form.items() if key not in IGNORED_FORM_FIELDS}

@app.route("/admin/usuarios", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            usuarios = Usuarios.query.all()
            extras['usarios'] = usuarios
        return render_template("database/usuarios.html", acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/usuarios.html", acao=acao, bloco=bloco)
    
@app.route("/admin/pessoas", methods=["GET", "POST"])
@admin_required
def gerenciar_pessoas():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
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
        elif acao == 'editar' and bloco == 0:
            pessoas_id_nome = db.session.query(Pessoas.id_pessoa, Pessoas.nome_pessoa).all()
            extras['pessoas'] = pessoas_id_nome
        elif acao == 'editar' and bloco == 1:
            id_pessoa = request.form.get('id_pessoa', None)
            pessoa = Pessoas.query.filter(Pessoas.id_pessoa == id_pessoa).first()
            extras['pessoa'] = pessoa
        return render_template("database/pessoas.html", acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/pessoas.html", acao=acao, bloco=bloco)

@app.route("/admin/usuario_especial")
@admin_required
def gerenciar_usuario_especial():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))

@app.route("/admin/aulas")
@admin_required
def gerenciar_aulas():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))

@app.route("/admin/laboratorios")
@admin_required
def gerenciar_laboratorios():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))

@app.route("/admin/reservas_fixa")
@admin_required
def gerenciar_reservas_fixa():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))

@app.route("/admin/permissoes")
@admin_required
def gerenciar_permissoes():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))