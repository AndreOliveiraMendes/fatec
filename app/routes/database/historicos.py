from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from app.models import db, Historicos
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import get_user_info

bp = Blueprint('historicos', __name__, url_prefix="/database")

@bp.route("/historicos", methods=["GET", "POST"])
@admin_required
def gerenciar_Historicos():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            historicos_paginados = Historicos.query.paginate(page=page, per_page=10, error_out=False)
            extras['historicos'] = historicos_paginados.items
            extras['pagination'] = historicos_paginados
    return render_template("database/historicos.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)