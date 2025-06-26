import copy
from main import app
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError
from models import db, Permissoes, Usuarios, Pessoas
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import none_if_empty, get_query_params, get_user_info, registrar_log_generico

@app.route("/admin/permissoes", methods=["GET", "POST"])
@admin_required
def gerenciar_permissoes():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            permissoes_paginadas = Permissoes.query.paginate(page=page, per_page=10, error_out=False)
            extras['permissoes'] = permissoes_paginadas.items
            extras['pagination'] = permissoes_paginadas
            extras['userid'] = userid
        elif acao == 'procurar' and bloco == 0:
            result = db.session.query(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas).all()
            extras['results'] = result
        elif acao == 'procurar' and bloco == 1:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
            flag_fixa = 1 if 'flag_fixa' in request.form else 0
            flag_temp = 2 if 'flag_temp' in request.form else 0
            flag_admin = 4 if 'flag_admin' in request.form else 0
            flag = flag_fixa|flag_temp|flag_admin
            modobusca = none_if_empty(request.form.get('modobusca')) 
            filter = []
            query_params = get_query_params(request)
            query = Permissoes.query
            if id_permissao_usuario:
                filter.append(Permissoes.id_permissao_usuario==id_permissao_usuario)
            if flag > 0:
                if modobusca == 'ou':
                    filter.append(Permissoes.permissao.bitwise_and(flag) > 0)
                else:
                    filter.append(Permissoes.permissao.bitwise_and(flag) == flag)
            if filter:
                permissoes_paginadas = query.filter(*filter).paginate(page=page, per_page=10, error_out=False)
                extras['permissoes'] = permissoes_paginadas.items
                extras['pagination'] = permissoes_paginadas
                extras['userid'] = userid
                extras['query_params'] = query_params
            else:
                result = db.session.query(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas).all()
                extras['results'] = result
                bloco = 0
                flash("especifique pelo menos um campo de busca", "danger")
        elif acao == 'inserir' and bloco == 0:
            usuarios_com_permissao = db.session.query(Permissoes.id_permissao_usuario)
            usuarios_sem_permissao = db.session.query(Usuarios.id_usuario, Pessoas.nome_pessoa).filter(~Usuarios.id_usuario.in_(usuarios_com_permissao)).join(Pessoas).all()
            extras['results'] = usuarios_sem_permissao
        elif acao == 'inserir' and bloco == 1:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
            flag_fixa = 1 if 'flag_fixa' in request.form else 0
            flag_temp = 2 if 'flag_temp' in request.form else 0
            flag_admin = 4 if 'flag_admin' in request.form else 0
            flag = flag_fixa|flag_temp|flag_admin
            try:
                nova_permissao = Permissoes(id_permissao_usuario=id_permissao_usuario, permissao=flag)
                db.session.add(nova_permissao)
                db.session.flush()  # garante ID
                registrar_log_generico(userid, "Inserção", nova_permissao)
                db.session.commit()
                flash("Permissao cadastrada com sucesso", "success")
            except IntegrityError as e:
                flash(f"Erro ao inserir pessoa: {str(e.orig)}", "danger")
                db.session.rollback()
            bloco = 0
            usuarios_com_permissao = db.session.query(Permissoes.id_permissao_usuario)
            usuarios_sem_permissao = db.session.query(Usuarios.id_usuario, Pessoas.nome_pessoa).filter(~Usuarios.id_usuario.in_(usuarios_com_permissao)).join(Pessoas).all()
            extras['results'] = usuarios_sem_permissao
        elif acao == 'editar' and bloco == 0:
            permissoes = db.session.query(Permissoes.id_permissao_usuario, Pessoas.nome_pessoa).select_from(Permissoes).join(Usuarios).join(Pessoas).all()
            extras['results'] = permissoes
        elif acao == 'editar' and bloco == 1:
            usuario = none_if_empty(request.form.get('id_usuario'))
            permissao = Permissoes.query.get(usuario)
            extras['permissao'] = permissao
            extras['userid'] = userid
        elif acao == 'editar' and bloco == 2:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
            flag_fixa = 1 if 'flag_fixa' in request.form else 0
            flag_temp = 2 if 'flag_temp' in request.form else 0
            flag_admin = 4 if 'flag_admin' in request.form else 0
            flag = flag_fixa|flag_temp|flag_admin
            
            permissao = Permissoes.query.get(id_permissao_usuario)
            if permissao:
                if id_permissao_usuario == userid and flag_admin == 0:
                    flash("voce não pode remover seu proprio poder de administrador", "danger")
                else:
                    try:
                        dados_anteriores = copy.copy(permissao)

                        permissao.permissao = flag

                        db.session.flush()  # Garante que o ID esteja atribuído

                        # Loga com os dados antigos + novos
                        registrar_log_generico(userid, "Edição", permissao, dados_anteriores)

                        db.session.commit()
                        flash("Permissao atualizada com sucesso", "success")
                    except IntegrityError as e:
                        db.session.rollback()
                        flash(f"Erro ao atualizar pessoa: {str(e.orig)}", "danger")
            else:
                flash("Permissao não encontrada", "danger")
            permissoes = db.session.query(Permissoes.id_permissao_usuario, Pessoas.nome_pessoa).select_from(Permissoes).join(Usuarios).join(Pessoas).all()
            extras['results'] = permissoes
            bloco = 0
            
        return render_template("database/permissoes.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/permissoes.html", username=username, perm=perm, acao=acao, bloco=bloco)