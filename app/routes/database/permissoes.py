import copy
from flask import Blueprint, flash, session, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Pessoas, Usuarios, Permissoes
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params, \
    registrar_log_generico_usuario, get_session_or_request, register_return
from app.auxiliar.constant import PERM_RESERVAS_FIXA, PERM_RESERVAS_TEMPORARIA, PERM_ADMIN
from app.auxiliar.dao import get_usuarios

bp = Blueprint('permissoes', __name__, url_prefix="/database")

def get_no_perm_users():
    sup = select(Permissoes.id_permissao_usuario)
    suwp = select(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas).filter(~Usuarios.id_usuario.in_(sup))
    return db.session.execute(suwp).all()

def get_perm(acao, userid):
    spupin = select(Permissoes.id_permissao_usuario, Pessoas.nome_pessoa).select_from(Permissoes).join(Usuarios).join(Pessoas)
    if acao == 'excluir':
        spupin = spupin.where(Permissoes.id_permissao_usuario!=userid)
    return db.session.execute(spupin).all()

def get_flag(request):
    flag_fixa = PERM_RESERVAS_FIXA if 'flag_fixa' in request.form else 0
    flag_temp = PERM_RESERVAS_TEMPORARIA if 'flag_temp' in request.form else 0
    flag_admin = PERM_ADMIN if 'flag_admin' in request.form else 0
    return flag_fixa|flag_temp|flag_admin

@bp.route("/permissoes", methods=["GET", "POST"])
@admin_required
def gerenciar_permissoes():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            sp = select(Permissoes)
            permissoes_paginadas = SelectPagination(select=sp, session=db.session, page=page, per_page=PER_PAGE, error_out=False)
            extras['permissoes'] = permissoes_paginadas.items
            extras['pagination'] = permissoes_paginadas
            extras['userid'] = userid

        elif acao == 'procurar' and bloco == 0:
            extras['users'] = get_usuarios()
        elif acao == 'procurar' and bloco == 1:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
            flag = get_flag(request)
            modobusca = none_if_empty(request.form.get('modobusca')) 
            filter = []
            query_params = get_query_params(request)
            if id_permissao_usuario is not None:
                filter.append(Permissoes.id_permissao_usuario==id_permissao_usuario)
            if flag > 0:
                if modobusca == 'ou':
                    filter.append(Permissoes.permissao.bitwise_and(flag) > 0)
                else:
                    filter.append(Permissoes.permissao.bitwise_and(flag) == flag)
            if filter:
                spf = select(Permissoes).where(*filter)
                permissoes_paginadas = SelectPagination(select=spf, session=db.session, page=page, per_page=PER_PAGE, error_out=False)
                extras['permissoes'] = permissoes_paginadas.items
                extras['pagination'] = permissoes_paginadas
                extras['userid'] = userid
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo", "danger")
                redirect_action, bloco = register_return('permissoes.gerenciar_permissoes', acao, extras, users=get_usuarios())

        elif acao == 'inserir' and bloco == 0:
            extras['users'] = get_no_perm_users()
        elif acao == 'inserir' and bloco == 1:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
            flag = get_flag(request)
            try:
                nova_permissao = Permissoes(id_permissao_usuario=id_permissao_usuario, permissao=flag)
                db.session.add(nova_permissao)
                db.session.flush()  # garante ID
                registrar_log_generico_usuario(userid, "Inserção", nova_permissao, observacao=f"0b{flag:03b}")
                db.session.commit()
                flash("Permissao cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                flash(f"Erro ao inserir pessoa: {str(e.orig)}", "danger")
                db.session.rollback()

            redirect_action, bloco = register_return('permissoes.gerenciar_permissoes', acao, extras, users=get_no_perm_users())

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['permissoes'] = get_perm(acao, userid)
        elif acao in ['editar', 'excluir'] and bloco == 1:
            usuario = none_if_empty(request.form.get('id_usuario'))
            permissao = db.get_or_404(Permissoes, usuario)
            extras['permissao'] = permissao
            extras['userid'] = userid
        elif acao == 'editar' and bloco == 2:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
            flag = get_flag(request)
            
            permissao = db.get_or_404(Permissoes, id_permissao_usuario)
            if id_permissao_usuario == userid and flag&PERM_ADMIN == 0:
                flash("voce não pode remover seu proprio poder de administrador", "danger")
            else:
                try:
                    dados_anteriores = copy.copy(permissao)
                    permissao.permissao = flag
                    db.session.flush()  # Garante que o ID esteja atribuído
                    observacao = f"0b{dados_anteriores.permissao:03b} → 0b{flag:03b}"
                    registrar_log_generico_usuario(userid, "Edição", permissao, dados_anteriores, observacao=observacao) # Loga com os dados antigos + novos
                    db.session.commit()
                    flash("Permissao atualizada com sucesso", "success")
                except (IntegrityError, OperationalError) as e:
                    db.session.rollback()
                    flash(f"Erro ao atualizar pessoa: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return('permissoes.gerenciar_permissoes', acao, extras, permissoes=get_perm(acao, userid))

        elif acao == 'excluir' and bloco == 2:
            id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)

            permissao = db.get_or_404(Permissoes, id_permissao_usuario)
            if id_permissao_usuario == userid:
                flash("voce não pode remover sua propria permissão", "danger")
            else:
                try:
                    db.session.flush()  # garante ID
                    registrar_log_generico_usuario(userid, "Exclusão", permissao, observacao=f"0b{permissao.permissao:03b}")

                    db.session.delete(permissao)
                    db.session.commit()
                    flash("Permissao excluída com sucesso", "success")

                except (IntegrityError, OperationalError) as e:
                    db.session.rollback()
                    flash(f"Erro ao excluir usuario: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return('permissoes.gerenciar_permissoes', acao, extras, permissoes=get_perm(acao, userid))
    if redirect_action:
        return redirect_action
    return render_template("database/permissoes.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)