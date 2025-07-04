from main import app
from flask import flash, session, render_template, request
from models import db, Laboratorios, DisponibilidadeEnum, TipoLaboratorioEnum
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
        if acao == 'listar':
            laboratorios_paginados = Laboratorios.query.paginate(page=page, per_page=10, error_out=False)
            extras['laboratorios'] = laboratorios_paginados.items
            extras['pagination'] = laboratorios_paginados
        return render_template("database/laboratorios.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/laboratorios.html", username=username, perm=perm, acao=acao, bloco=bloco)