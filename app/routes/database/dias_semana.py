import copy

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (disable_action,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_dias_da_semana
from app.auxiliar.decorators import admin_required
from app.models import Dias_da_Semana, db
from config.general import PER_PAGE

bp = Blueprint('database_dias_da_semana', __name__, url_prefix="/database")

@bp.route("/dias_da_semana", methods=["GET", "POST"])
@admin_required
def gerenciar_dias_da_semana():
    url = 'database_dias_da_semana.gerenciar_dias_da_semana'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user_info(userid)
    disabled = ['procurar']
    extras = {'url':url}
    disable_action(extras, disabled)
    if request.method == 'POST':
        if acao in disabled:
            abort(403, description="Esta funcionalidade não foi implementada.")

        if acao == 'listar':
            sel_dias_semana = select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
            dias_da_semana_paginada = SelectPagination(
                select=sel_dias_semana, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['dias_da_semana'] = dias_da_semana_paginada.items
            extras['pagination'] = dias_da_semana_paginada

        elif acao == 'inserir' and bloco == 1:
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            nome_semana = none_if_empty(request.form.get('nome_semana', None))
            try:
                nova_semana = Dias_da_Semana(id_semana = id_semana, nome_semana = nome_semana)
                db.session.add(nova_semana)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_semana)

                db.session.commit()
                flash("Semana cadastrada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Falah ao cadastrar semana:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras)

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['dias_da_semana'] = get_dias_da_semana()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            dia_da_semana = db.get_or_404(Dias_da_Semana, id_semana)
            extras['dia_semana'] = dia_da_semana
        elif acao == 'editar' and bloco == 2:
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            nome_semana = none_if_empty(request.form.get('nome_semana'))
            dia_da_semana = db.get_or_404(Dias_da_Semana, id_semana)
            try:
                dados_anteriores = copy.copy(dia_da_semana)
                dia_da_semana.nome_semana = nome_semana

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', dia_da_semana, dados_anteriores)

                db.session.commit()
                flash("Dia da semana editado com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao editar dia da semana:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras, dias_da_semana=get_dias_da_semana())
        elif acao == 'excluir' and bloco == 2:
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            dia_da_semana = db.get_or_404(Dias_da_Semana, id_semana)
            try:
                db.session.delete(dia_da_semana)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', dia_da_semana)

                db.session.commit()
                flash("Dia da semana excluido com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"erro ao excluir dia da semana:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return(url, acao, extras, dias_da_semana=get_dias_da_semana())
    if redirect_action:
        return redirect_action
    return render_template("database/table/dias_da_semana.html", username=user.username, perm=user.perm, acao=acao, bloco=bloco, **extras)