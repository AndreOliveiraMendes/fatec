import copy
from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for, abort
from sqlalchemy.exc import IntegrityError
from config import PER_PAGE
from app.models import db, DiasSemana
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, get_query_params, registrar_log_generico, disable_action

bp = Blueprint('dias_semanas', __name__, url_prefix="/database")

def get_dias_semana():
    return db.session.query(DiasSemana.id, DiasSemana.nome).order_by(DiasSemana.id).all()

@bp.route("/dias_semanas", methods=["GET", "POST"])
@admin_required
def gerenciar_dias_semana():
    acao = request.form.get('acao', 'abertura')
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
            dias_semana_paginada = DiasSemana.query.order_by(DiasSemana.id).paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['dias_semana'] = dias_semana_paginada.items
            extras['pagination'] = dias_semana_paginada
        elif acao == 'inserir' and bloco == 1:
            id = none_if_empty(request.form.get('id'), int)
            nome = none_if_empty(request.form.get('nome', None))
            try:
                nova_semana = DiasSemana(id = id, nome = nome)
                db.session.add(nova_semana)

                db.session.flush()
                registrar_log_generico(userid, 'Inserção', nova_semana)

                db.session.commit()
                flash("Semana cadastrada com sucesso", "success")
            except IntegrityError as e:
                db.session.rollback()
                flash(f"Falah ao cadastrar semana:{str(e.orig)}", "danger")
            
            bloco = 0
        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['dias_semana'] = get_dias_semana()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id = none_if_empty(request.form.get('id'), int)
            dia_da_semana = DiasSemana.query.get_or_404(id)
            extras['dia_semana'] = dia_da_semana
        elif acao == 'editar' and bloco == 2:
            id = none_if_empty(request.form.get('id'), int)
            nome = none_if_empty(request.form.get('nome'))
            dia_da_semana = DiasSemana.query.get_or_404(id)
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
            
            bloco = 0
            extras['dias_semana'] = get_dias_semana()
        elif acao == 'excluir' and bloco == 2:
            id = none_if_empty(request.form.get('id'), int)
            dia_da_semana = DiasSemana.query.get_or_404(id)
            try:
                db.session.delete(dia_da_semana)

                db.session.flush()
                registrar_log_generico(userid, 'Exclusão', dia_da_semana)

                db.session.commit()
                flash("Dia da semana excluido com sucesso", "success")
            except IntegrityError as e:
                db.session.rollback()
                flash(f"erro ao excluir dia da semana:{str(e.orig)}", "danger")

            bloco = 0
            extras['dias_semana'] = get_dias_semana()
    return render_template("database/dias_semanas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)