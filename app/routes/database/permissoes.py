import copy
from app.main import app
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError
from app.models import db, Permissoes, Usuarios, Pessoas
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, get_query_params, get_user_info, registrar_log_generico
from app.auxiliar.constant import PERM_RESERVAS_FIXA, PERM_RESERVAS_TEMPORARIA, PERM_ADMIN

def get_no_perm_users():
    usuarios_com_permissao = db.session.query(Permissoes.id_permissao_usuario)
    return db.session.query(Usuarios.id_usuario, Pessoas.nome_pessoa).filter(~Usuarios.id_usuario.in_(usuarios_com_permissao)).join(Pessoas).all()

def get_users():
    return db.session.query(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas).all()

def get_perm(acao, userid):
    perm = db.session.query(Permissoes.id_permissao_usuario, Pessoas.nome_pessoa).select_from(Permissoes).join(Usuarios).join(Pessoas)
    if acao == 'excluir':
        perm = perm.filter(Permissoes.id_permissao_usuario!=userid)
    return perm.all()

def get_flag(request):
    flag_fixa = PERM_RESERVAS_FIXA if 'flag_fixa' in request.form else 0
    flag_temp = PERM_RESERVAS_TEMPORARIA if 'flag_temp' in request.form else 0
    flag_admin = PERM_ADMIN if 'flag_admin' in request.form else 0
    return flag_fixa|flag_temp|flag_admin

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
            extras['users'] = get_users()
        elif acao == 'procurar' and bloco == 1:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
            flag = get_flag(request)
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
                extras['users'] = get_users()
                bloco = 0
                flash("especifique pelo menos um campo de busca", "danger")
        elif acao == 'inserir' and bloco == 0:
            extras['users'] = get_no_perm_users()
        elif acao == 'inserir' and bloco == 1:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
            flag = get_flag(request)
            try:
                nova_permissao = Permissoes(id_permissao_usuario=id_permissao_usuario, permissao=flag)
                db.session.add(nova_permissao)
                db.session.flush()  # garante ID
                registrar_log_generico(userid, "Inserção", nova_permissao, observacao=f"0b{flag:03b}")
                db.session.commit()
                flash("Permissao cadastrada com sucesso", "success")
            except IntegrityError as e:
                flash(f"Erro ao inserir pessoa: {str(e.orig)}", "danger")
                db.session.rollback()
            bloco = 0
            extras['users'] = get_no_perm_users()
        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['permissoes'] = get_perm(acao, userid)
        elif acao in ['editar', 'excluir'] and bloco == 1:
            usuario = none_if_empty(request.form.get('id_usuario'))
            permissao = Permissoes.query.get_or_404(usuario)
            extras['permissao'] = permissao
            extras['userid'] = userid
        elif acao == 'editar' and bloco == 2:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
            flag = get_flag(request)
            
            permissao = Permissoes.query.get_or_404(id_permissao_usuario)
            if id_permissao_usuario == userid and flag&PERM_ADMIN == 0:
                flash("voce não pode remover seu proprio poder de administrador", "danger")
            else:
                try:
                    dados_anteriores = copy.copy(permissao)
                    permissao.permissao = flag
                    db.session.flush()  # Garante que o ID esteja atribuído
                    observacao = f"0b{dados_anteriores.permissao:03b} → 0b{flag:03b}"
                    registrar_log_generico(userid, "Edição", permissao, dados_anteriores, observacao=observacao) # Loga com os dados antigos + novos
                    db.session.commit()
                    flash("Permissao atualizada com sucesso", "success")
                except IntegrityError as e:
                    db.session.rollback()
                    flash(f"Erro ao atualizar pessoa: {str(e.orig)}", "danger")
            extras['permissoes'] = get_perm(acao, userid)
            bloco = 0
        elif acao == 'excluir' and bloco == 2:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)

            permissao = Permissoes.query.get_or_404(id_permissao_usuario)
            if id_permissao_usuario == userid:
                flash("voce não pode remover sua propria permissão", "danger")
            else:
                try:
                    db.session.flush()  # garante ID
                    registrar_log_generico(userid, "Exclusão", permissao, observacao=f"0b{permissao.permissao:03b}")

                    db.session.delete(permissao)
                    db.session.commit()
                    flash("Permissao excluída com sucesso", "success")

                except IntegrityError as e:
                    db.session.rollback()
                    flash(f"Erro ao excluir usuario: {str(e.orig)}", "danger")

            extras['permissoes'] = get_perm(acao, userid)
            bloco = 0
        return render_template("database/permissoes.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/permissoes.html", username=username, perm=perm, acao=acao, bloco=bloco)