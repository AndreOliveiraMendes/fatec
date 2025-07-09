import copy
from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for, abort
from sqlalchemy.exc import IntegrityError
from config import PER_PAGE
from app.models import db, Turnos
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, get_query_params, registrar_log_generico, disable_action

bp = Blueprint('turnos', __name__, url_prefix="/database")

@bp.route("/turnos", methods=["GET", "POST"])
@admin_required
def gerenciar_turnos():
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
    return render_template("database/turnos.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)