from main import app
from flask import flash, session, render_template, request
from models import db, Permissoes
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import get_user_info

@app.route("/admin/permissoes", methods=["GET", "POST"])
@admin_required
def gerenciar_permissoes():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        return render_template("database/permissoes.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/permissoes.html", username=username, perm=perm, acao=acao, bloco=bloco)