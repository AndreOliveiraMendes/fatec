import copy
from typing import Any

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.usuarios import get_pessoas, get_user, get_usuarios
from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.usuarios import Usuarios
from app.routes_helper.request import get_query_params, get_session_or_request
from app.routes_helper.ui import disable_action
from config.database_views import get_url
from config.general import PER_PAGE

bp = Blueprint('database_usuarios', __name__, url_prefix="/database")

@bp.route("/usuarios", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios():
    url = get_url('database_usuarios')
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    disabled = ['inserir', 'editar', 'excluir']
    extras: dict[str, Any] = {'url':url}
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
            filters = []
            query_params = get_query_params(request)
            if id_usuario is not None:
                filters.append(Usuarios.id_usuario == id_usuario)
            if id_pessoa is not None:
                filters.append(Usuarios.id_pessoa == id_pessoa)
            if tipo_pessoa:
                filters.append(Usuarios.tipo_pessoa == tipo_pessoa)
            if situacao_pessoa:
                filters.append(Usuarios.situacao_pessoa == situacao_pessoa)
            if grupo_pessoa:
                filters.append(Usuarios.grupo_pessoa == grupo_pessoa)
            if filters:
                sel_users = select(Usuarios).where(*filters)
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
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao cadastrar usuario")

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
            id_pessoa = get_value_or_abort(request.form.get('id_pessoa', None), 400, "O campo 'id_pessoa' é obrigatório.", int)
            tipo_pessoa = get_value_or_abort(request.form.get('tipo_pessoa', None), 400, "O campo 'tipo_pessoa' é obrigatório.")
            situacao_pessoa = get_value_or_abort(request.form.get('situacao_pessoa', None), 400, "O campo 'situacao_pessoa' é obrigatório.")
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
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar usuario")

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

                except DB_ERRORS as e:
                    handle_db_error(e, "Erro ao excluir usuario")

            redirect_action, bloco = register_return(url,
                acao, extras, usuarios=get_usuarios(acao, userid))
    if redirect_action:
        return redirect_action
    return render_template("database/table/usuarios.html",
        user=user, acao=acao, bloco=bloco, **extras)