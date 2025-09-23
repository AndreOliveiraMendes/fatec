import copy

from flask import Blueprint, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_query_params,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_usuarios_especiais
from app.auxiliar.decorators import admin_required
from app.models import Usuarios_Especiais, db
from config.general import PER_PAGE

bp = Blueprint('database_usuarios_especiais', __name__, url_prefix="/database")

@bp.route("/usuarios_especiais", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios_especiais():
    url = 'database_usuarios_especiais.gerenciar_usuarios_especiais'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user_info(userid)
    extras = {'url':url}
    if request.method == 'POST':
        if acao == "listar":
            sel_users = select(Usuarios_Especiais)
            usuarios_especiais_paginados = SelectPagination(
                select=sel_users, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['usuarios_especiais'] = usuarios_especiais_paginados.items
            extras['pagination'] = usuarios_especiais_paginados

        elif acao == 'procurar' and bloco == 1:
            id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)
            nome_usuario_especial = none_if_empty(request.form.get('nome_usuario_especial'))
            exact_name_match = 'emnome' in request.form
            filter = []
            query_params = get_query_params(request)
            if id_usuario_especial is not None:
                filter.append(Usuarios_Especiais.id_usuario_especial == id_usuario_especial)
            if nome_usuario_especial:
                if exact_name_match:
                    filter.append(Usuarios_Especiais.nome_usuario_especial == nome_usuario_especial)
                else:
                    filter.append(
                        Usuarios_Especiais.nome_usuario_especial.ilike(f"%{nome_usuario_especial}%"))
            if filter:
                sel_users = select(Usuarios_Especiais).where(*filter)
                usuarios_especiais_paginados = SelectPagination(
                    select=sel_users, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['usuarios_especiais'] = usuarios_especiais_paginados.items
                extras['pagination'] = usuarios_especiais_paginados
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(
                    url, acao, extras)

        elif acao == 'inserir' and bloco == 1:
            nome_usuario_especial = none_if_empty(request.form.get('nome_usuario_especial'))
            try:
                novo_usuario_especial = Usuarios_Especiais(nome_usuario_especial=nome_usuario_especial)
                db.session.add(novo_usuario_especial)
                db.session.flush()
                registrar_log_generico_usuario(userid, "Inserção", novo_usuario_especial)
                db.session.commit()
                flash("Usuario Especial cadastrada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao inserir usuario especial: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras)

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['usuarios_especiais'] = get_usuarios_especiais()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)
            usuario_especial = db.get_or_404(Usuarios_Especiais, id_usuario_especial)
            extras['usuario_especial'] = usuario_especial
        elif acao == 'editar' and bloco == 2:
            id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)
            nome_usuario_especial = none_if_empty(request.form.get('nome_usuario_especial'))

            usuario_especial = db.get_or_404(Usuarios_Especiais, id_usuario_especial)
            try:
                dados_anteriores = copy.copy(usuario_especial)

                usuario_especial.nome_usuario_especial = nome_usuario_especial

                db.session.flush()  # garante ID
                registrar_log_generico_usuario(userid, "Edição", usuario_especial, dados_anteriores)

                db.session.commit()
                flash("Usuario especial editado com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao editar usuario especial: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, usuarios_especiais=get_usuarios_especiais())
        elif acao == 'excluir' and bloco == 2:
            id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)

            usuario_especial = db.get_or_404(Usuarios_Especiais, id_usuario_especial)
            try:
                db.session.delete(usuario_especial)

                db.session.flush()  # garante ID
                registrar_log_generico_usuario(userid, "Exclusão", usuario_especial)

                db.session.commit()
                flash("Usuario especial excluido com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir usuario especial: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, usuarios_especiais=get_usuarios_especiais())
    if redirect_action:
        return redirect_action
    return render_template("database/table/usuarios_especiais.html",
        username=user.username, perm=user.perm, acao=acao, bloco=bloco, **extras)