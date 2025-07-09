from flask import Blueprint
from flask import flash, session, render_template, request, abort
from sqlalchemy.exc import IntegrityError
from config import PER_PAGE
from app.models import db, Turnos
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, \
    registrar_log_generico, disable_action, get_session_or_request, register_return

bp = Blueprint('turnos', __name__, url_prefix="/database")

@bp.route("/turnos", methods=["GET", "POST"])
@admin_required
def gerenciar_turnos():
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
            turnos_paginados = Turnos.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['turnos'] = turnos_paginados.items
            extras['pagination'] = turnos_paginados

        elif acao == 'inserir' and bloco == 1:
            nome = none_if_empty(request.form.get('nome'))
            horario_inicio = parse_time_string(request.form.get('horario_inicio'))
            horario_fim = parse_time_string(request.form.get('horario_fim'))
            try:
                novo_turno = Turnos(nome = nome, horario_inicio = horario_inicio, horario_fim = horario_fim)
                db.session.add(novo_turno)

                db.session.flush()
                registrar_log_generico(userid, 'Inserção', novo_turno)

                db.session.commit()
                flash("Turno cadastrado com sucesso", "success")
            except IntegrityError as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar turno:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return('turnos.gerenciar_turnos', acao, extras)

    if redirect_action:
        return redirect_action
    return render_template("database/turnos.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)