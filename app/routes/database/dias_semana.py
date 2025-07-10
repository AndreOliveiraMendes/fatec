import copy
from flask import Blueprint
from flask import flash, session, render_template, request, abort
from sqlalchemy.exc import IntegrityError
from config import PER_PAGE
from app.models import db, Dias_da_Semana
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, get_user_info, registrar_log_generico,\
    disable_action, get_session_or_request, register_return

bp = Blueprint('dias_da_semana', __name__, url_prefix="/database")

def get_dias_da_semana():
    return db.session.query(Dias_da_Semana.id, Dias_da_Semana.nome).order_by(Dias_da_Semana.id).all()

@bp.route("/dias_da_semana", methods=["GET", "POST"])
@admin_required
def gerenciar_dias_da_semana():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    disabled = ['procurar']
    extras = {}
    disable_action(extras, disabled)
    if request.method == 'POST':
        if acao in disabled:
            abort(403, description="Esta funcionalidade não foi implementada.")

        if acao == 'listar':
            dias_da_semana_paginada = Dias_da_Semana.query.order_by(Dias_da_Semana.id).paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['dias_da_semana'] = dias_da_semana_paginada.items
            extras['pagination'] = dias_da_semana_paginada

        elif acao == 'inserir' and bloco == 1:
            id = none_if_empty(request.form.get('id'), int)
            nome = none_if_empty(request.form.get('nome', None))
            try:
                nova_semana = Dias_da_Semana(id = id, nome = nome)
                db.session.add(nova_semana)

                db.session.flush()
                registrar_log_generico(userid, 'Inserção', nova_semana)

                db.session.commit()
                flash("Semana cadastrada com sucesso", "success")
            except IntegrityError as e:
                db.session.rollback()
                flash(f"Falah ao cadastrar semana:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return('dias_da_semana.gerenciar_dias_da_semana', acao, extras)

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['dias_da_semana'] = get_dias_da_semana()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id = none_if_empty(request.form.get('id'), int)
            dia_da_semana = Dias_da_Semana.query.get_or_404(id)
            extras['dia_semana'] = dia_da_semana
        elif acao == 'editar' and bloco == 2:
            id = none_if_empty(request.form.get('id'), int)
            nome = none_if_empty(request.form.get('nome'))
            dia_da_semana = Dias_da_Semana.query.get_or_404(id)
            try:
                dados_anteriores = copy.copy(dia_da_semana)
                dia_da_semana.nome = nome

                db.session.flush()
                registrar_log_generico(userid, 'Edição', dia_da_semana, dados_anteriores)

                db.session.commit()
                flash("Dia da semana editado com sucesso", "success")
            except IntegrityError as e:
                db.session.rollback()
                flash(f"Erro ao editar dia da semana:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return('dias_da_semana.gerenciar_dias_da_semana', acao, extras, dias_da_semana=get_dias_da_semana())
        elif acao == 'excluir' and bloco == 2:
            id = none_if_empty(request.form.get('id'), int)
            dia_da_semana = Dias_da_Semana.query.get_or_404(id)
            try:
                db.session.delete(dia_da_semana)

                db.session.flush()
                registrar_log_generico(userid, 'Exclusão', dia_da_semana)

                db.session.commit()
                flash("Dia da semana excluido com sucesso", "success")
            except IntegrityError as e:
                db.session.rollback()
                flash(f"erro ao excluir dia da semana:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return('dias_da_semana.gerenciar_dias_da_semana', acao, extras, dias_da_semana=get_dias_da_semana())
    if redirect_action:
        return redirect_action
    return render_template("database/dias_da_semana.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)