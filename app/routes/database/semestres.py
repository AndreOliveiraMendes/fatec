from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from app.models import db, Semestres
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params, registrar_log_generico

bp = Blueprint('semestres', __name__, url_prefix="/database")

@bp.route("/semestres", methods=["GET", "POST"])
@admin_required
def gerenciar_semestres():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        pass
    return render_template("database/semestres.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)