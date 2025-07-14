import copy
from flask import Blueprint
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Usuarios_Especiais
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params, \
    registrar_log_generico_usuario, get_session_or_request, register_return


bp = Blueprint('usuarios_especiais', __name__, url_prefix="/database")

def get_usuarios_especiais():
    return db.session.query(Usuarios_Especiais.id_usuario_especial, Usuarios_Especiais.nome_usuario_especial).all()

@bp.route("/usuarios_especiais", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios_especiais():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == "listar":
            usuarios_especiais_paginados = Usuarios_Especiais.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['usuarios_especiais'] = usuarios_especiais_paginados.items
            extras['pagination'] = usuarios_especiais_paginados

        elif acao == 'procurar' and bloco == 1:
            id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)
            nome_usuario_especial = none_if_empty(request.form.get('nome_usuario_especial'))
            exact_name_match = 'emnome' in request.form
            filter = []
            query_params = get_query_params(request)
            query = Usuarios_Especiais.query
            if id_usuario_especial is not None:
                filter.append(Usuarios_Especiais.id_usuario_especial == id_usuario_especial)
            if nome_usuario_especial:
                if exact_name_match:
                    filter.append(Usuarios_Especiais.nome_usuario_especial == nome_usuario_especial)
                else:
                    filter.append(Usuarios_Especiais.nome_usuario_especial.ilike(f"%{nome_usuario_especial}%"))
            if filter:
                usuarios_especiais_paginados = query.filter(*filter).paginate(page=page, per_page=PER_PAGE, error_out=False)
                extras['usuarios_especiais'] = usuarios_especiais_paginados.items
                extras['pagination'] = usuarios_especiais_paginados
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return('usuarios_especiais.gerenciar_usuarios_especiais', acao, extras)

        elif acao == 'inserir' and bloco == 1:
            nome_usuario_especial = none_if_empty(request.form.get('nome_usuario_especial'))
            try:
                novo_usuario_especial = Usuarios_Especiais(nome_usuario_especial=nome_usuario_especial)
                db.session.add(novo_usuario_especial)
                db.session.flush()
                registrar_log_generico_usuario(userid, "Inserção", novo_usuario_especial)
                db.session.commit()
                flash("Usuario Especial cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                flash(f"Erro ao inserir usuario especial: {str(e.orig)}", "danger")
                db.session.rollback()

            redirect_action, bloco = register_return('usuarios_especiais.gerenciar_usuarios_especiais', acao, extras)

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['usuarios_especiais'] = get_usuarios_especiais()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)
            usuario_especial = Usuarios_Especiais.query.get_or_404(id_usuario_especial)
            extras['usuario_especial'] = usuario_especial
        elif acao == 'editar' and bloco == 2:
            id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)
            nome_usuario_especial = none_if_empty(request.form.get('nome_usuario_especial'))

            usuario_especial = Usuarios_Especiais.query.get_or_404(id_usuario_especial)
            try:
                dados_anteriores = copy.copy(usuario_especial)

                usuario_especial.nome_usuario_especial = nome_usuario_especial

                db.session.flush()  # garante ID
                registrar_log_generico_usuario(userid, "Edição", usuario_especial, dados_anteriores)

                db.session.commit()
                flash("Usuario especial editado com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao editar usuario especial: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return('usuarios_especiais.gerenciar_usuarios_especiais', acao, extras, usuarios_especiais=get_usuarios_especiais())
        elif acao == 'excluir' and bloco == 2:
            id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)

            usuario_especial = Usuarios_Especiais.query.get_or_404(id_usuario_especial)
            try:
                db.session.delete(usuario_especial)

                db.session.flush()  # garante ID
                registrar_log_generico_usuario(userid, "Exclusão", usuario_especial)

                db.session.commit()
                flash("Usuario especial excluido com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir usuario especial: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return('usuarios_especiais.gerenciar_usuarios_especiais', acao, extras, usuarios_especiais=get_usuarios_especiais())
    if redirect_action:
        return redirect_action
    return render_template("database/usuarios_especiais.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)