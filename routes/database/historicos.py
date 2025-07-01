from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Historicos
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import get_user_info

@app.route("/admin/historico", methods=["GET", "POST"])
@admin_required
def gerenciar_Historico():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            historicos_paginados = Historicos.query.paginate(page=page, per_page=10, error_out=False)
            extras['historicos'] = historicos_paginados.items
            extras['pagination'] = historicos_paginados
        return render_template("database/historicos.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/historicos.html", username=username, perm=perm, acao=acao, bloco=bloco)