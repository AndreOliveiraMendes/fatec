from main import app
from flask import flash, session, render_template, request
from models import db, Laboratorios
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params, registrar_log_generico

@app.route("/admin/laboratorios", methods=["GET", "POST"])
@admin_required
def gerenciar_laboratorios():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        return render_template("database/laboratorios.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/laboratorios.html", username=username, perm=perm, acao=acao, bloco=bloco)