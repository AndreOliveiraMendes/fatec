import copy

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (disable_action, get_query_params,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_pessoas, get_usuarios
from app.auxiliar.decorators import admin_required
from app.models import Usuarios, db
from config.general import PER_PAGE

bp = Blueprint('database_usuarios', __name__, url_prefix="/database")

@bp.route("/usuarios", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios():
    url = 'database_usuarios.gerenciar_usuarios'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user_info(userid)
    disabled = ['inserir', 'editar', 'excluir']
    extras = {'url':url}
    disable_action(extras, disabled)
    if request.method == 'POST':
        if acao in disabled:
            abort(403, description="Esta funcionalidade está desabilitada no momento.")

        if acao == 'listar':
            sel_users = select(Usuarios)
            usuarios_paginados = SelectPagination(
                select=sel_users, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['usuarios'] = usuarios_paginados.items
            extras['pagination'] = usuarios_paginados
            extras['userid'] = userid

        elif acao == 'procurar' and bloco == 0:
            extras['pessoas'] = get_pessoas()
        elif acao == 'procurar' and bloco == 1:
            id_usuario = none_if_empty(request.form.get('id_usuario', None), int)
            id_pessoa = none_if_empty(request.form.get('id_pessoa', None), int)
            tipo_pessoa = none_if_empty(request.form.get('tipo_pessoa', None))
            situacao_pessoa = none_if_empty(request.form.get('situacao_pessoa', None))
            grupo_pessoa = none_if_empty(request.form.get('grupo_pessoa', None))
            filter = []
            query_params = get_query_params(request)
            if id_usuario is not None:
                filter.append(Usuarios.id_usuario == id_usuario)
            if id_pessoa is not None:
                filter.append(Usuarios.id_pessoa == id_pessoa)
            if tipo_pessoa:
                filter.append(Usuarios.tipo_pessoa == tipo_pessoa)
            if situacao_pessoa:
                filter.append(Usuarios.situacao_pessoa == situacao_pessoa)
            if grupo_pessoa:
                filter.append(Usuarios.grupo_pessoa == grupo_pessoa)
            if filter:
                sel_users = select(Usuarios).where(*filter)
                usuarios_paginados = SelectPagination(
                    select=sel_users, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['usuarios'] = usuarios_paginados.items
                extras['pagination'] = usuarios_paginados
                extras['userid'] = userid
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(url,
                    acao, extras, pessoas=get_pessoas())

        elif acao == 'inserir' and bloco == 0:
            extras['pessoas'] = get_pessoas()
        elif acao == 'inserir' and bloco == 1:
            id_usuario = none_if_empty(request.form.get('id_usuario', None), int)
            id_pessoa = none_if_empty(request.form.get('id_pessoa', None), int)
            tipo_pessoa = none_if_empty(request.form.get('tipo_pessoa', None))
            situacao_pessoa = none_if_empty(request.form.get('situacao_pessoa', None))
            grupo_pessoa = none_if_empty(request.form.get('grupo_pessoa', None))
            try:
                novo_usuario = Usuarios(
                    id_usuario=id_usuario, id_pessoa=id_pessoa, tipo_pessoa=tipo_pessoa,
                    situacao_pessoa=situacao_pessoa, grupo_pessoa=grupo_pessoa)
                db.session.add(novo_usuario)
                db.session.flush()  # garante ID
                registrar_log_generico_usuario(userid, "Inserção", novo_usuario)
                db.session.commit()
                flash("Usuario cadastrado com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao inserir usuario: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, pessoas=get_pessoas())

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['usuarios'] = get_usuarios(acao, userid)
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_usuario = none_if_empty(request.form.get('id_usuario', None))
            user = db.get_or_404(Usuarios, id_usuario)
            extras['usuario'] = user
            extras['pessoas'] = get_pessoas()
        elif acao == 'editar' and bloco == 2:
            id_usuario = none_if_empty(request.form.get('id_usuario', None), int)
            id_pessoa = none_if_empty(request.form.get('id_pessoa', None), int)
            tipo_pessoa = none_if_empty(request.form.get('tipo_pessoa', None))
            situacao_pessoa = none_if_empty(request.form.get('situacao_pessoa', None))
            grupo_pessoa = none_if_empty(request.form.get('grupo_pessoa', None))

            usuario = db.get_or_404(Usuarios, id_usuario)

            try:
                dados_anteriores = copy.copy(usuario)

                usuario.id_pessoa = id_pessoa
                usuario.tipo_pessoa = tipo_pessoa
                usuario.situacao_pessoa = situacao_pessoa
                usuario.grupo_pessoa = grupo_pessoa

                db.session.flush()  # Garante que o ID esteja atribuído

                registrar_log_generico_usuario(userid, "Edição", usuario, dados_anteriores)

                db.session.commit()
                flash("Usuario atualizado com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao atualizar usuario: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, usuarios=get_usuarios(acao, userid))
        elif acao == 'excluir' and bloco == 2:
            id_usuario = none_if_empty(request.form.get('id_usuario', None), int)
            
            user = db.get_or_404(Usuarios, id_usuario)

            if userid == id_usuario:
                flash("Voce não pode se excluir", "danger")
            else:
                try:
                    db.session.flush()  # garante ID
                    registrar_log_generico_usuario(userid, "Exclusão", user)

                    db.session.delete(user)
                    db.session.commit()
                    flash("Usuario excluído com sucesso", "success")

                except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                    db.session.rollback()
                    flash(f"Erro ao excluir usuario: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, usuarios=get_usuarios(acao, userid))
    if redirect_action:
        return redirect_action
    return render_template("database/table/usuarios.html",
        username=user.username, perm=user.perm, acao=acao, bloco=bloco, **extras)