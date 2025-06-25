from main import app
from flask import flash, session, render_template, request, redirect, url_for
from sqlalchemy.exc import IntegrityError
from models import db, Usuarios, Pessoas
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import none_if_empty, get_query_params, get_user_info
from sqlalchemy.orm import joinedload

@app.route("/admin/usuarios", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            usuarios_paginados = Usuarios.query.paginate(page=page, per_page=10, error_out=False)
            extras['usuarios'] = usuarios_paginados.items
            extras['pagination'] = usuarios_paginados
            extras['userid'] = userid
        elif acao == 'procurar' and bloco == 1:
            id_usuario = none_if_empty(request.form.get('id_usuario', None))
            id_pessoa = none_if_empty(request.form.get('id_pessoa', None))
            tipo_pessoa = none_if_empty(request.form.get('tipo_pessoa', None))
            situacao_pessoa = none_if_empty(request.form.get('situacao_pessoa', None))
            grupo_pessoa = none_if_empty(request.form.get('grupo_pessoa', None))
            filter = []
            query_params = get_query_params(request)
            query = Usuarios.query
            if id_usuario:
                filter.append(Usuarios.id_usuario == id_usuario)
            if id_pessoa:
                filter.append(Usuarios.id_pessoa == id_pessoa)
            if tipo_pessoa:
                filter.append(Usuarios.tipo_pessoa == tipo_pessoa)
            if situacao_pessoa:
                filter.append(Usuarios.situacao_pessoa == situacao_pessoa)
            if grupo_pessoa:
                filter.append(Usuarios.grupo_pessoa == grupo_pessoa)
            if filter:
                usuarios_paginados = query.filter(*filter).paginate(page=page, per_page=10, error_out=False)
                extras['usuarios'] = usuarios_paginados.items
                extras['pagination'] = usuarios_paginados
                extras['userid'] = userid
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                bloco = 0
        elif acao == 'inserir' and bloco == 0:
            pessoas_id_nome = db.session.query(Pessoas.id_pessoa, Pessoas.nome_pessoa).all()
            extras['pessoas'] = pessoas_id_nome
        elif acao == 'inserir' and bloco == 1:
            id_usuario = none_if_empty(request.form.get('id_usuario', None))
            id_pessoa = none_if_empty(request.form.get('id_pessoa', None))
            tipo_pessoa = none_if_empty(request.form.get('tipo_pessoa', None))
            situacao_pessoa = none_if_empty(request.form.get('situacao_pessoa', None))
            grupo_pessoa = none_if_empty(request.form.get('grupo_pessoa', None))
            try:
                novo_usuario = Usuarios(id_usuario=id_usuario, id_pessoa=id_pessoa, tipo_pessoa=tipo_pessoa, situacao_pessoa=situacao_pessoa, grupo_pessoa=grupo_pessoa)
                db.session.add(novo_usuario)
                db.session.flush()  # garante ID
                registrar_log_generico(userid, "Inserção", novo_usuario)
                db.session.commit()
                flash("Usuario cadastrado com sucesso", "success")
            except IntegrityError as e:
                flash(f"Erro ao inserir usuario: {str(e.orig)}", "danger")
                db.session.rollback()
            pessoas_id_nome = db.session.query(Pessoas.id_pessoa, Pessoas.nome_pessoa).all()
            extras['pessoas'] = pessoas_id_nome
            bloco = 0
        elif acao == 'editar' and bloco == 0:
            result = db.session.query(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas, Usuarios.id_pessoa == Pessoas.id_pessoa).all()
            extras['results'] = result
        elif acao == 'editar' and bloco == 1:
            id_usuario = none_if_empty(request.form.get('id_usuario', None))
            
        return render_template("database/usuarios.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/usuarios.html", username=username, perm=perm, acao=acao, bloco=bloco)