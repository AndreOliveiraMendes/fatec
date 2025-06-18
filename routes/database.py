from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Reservas_Fixa, Usuarios, Pessoas, Usuarios_Permissao, Laboratorios, Aulas
from decorators import admin_required

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
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            pessoas = Pessoas.query.all()
            extras['pessoas'] = pessoas
        elif acao == 'procurar' and bloco == 1:
            id = request.form.get('id_pessoa', None)
            nome = request.form.get('nome', None)
            exact_name_match = 'emnome' in request.form
            email = request.form.get('email', None)
            exact_email_match = 'ememail' in request.form
            filter = []
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
                query = query.filter(*filter)
                extras['pessoas'] = query.all()
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                bloco = 0
        elif acao == 'inserir' and bloco == 1:
            nome = request.form.get('nome', None)
            email = request.form.get('email', None)
            nova_pessoa = Pessoas(nome_pessoa=nome, email_pessoa=email)
            db.session.add(nova_pessoa)
            db.session.commit()
            flash("Pessoa cadastrada com sucesso", "success")
            bloco = 0
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