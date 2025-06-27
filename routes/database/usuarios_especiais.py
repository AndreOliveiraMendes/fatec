import requests
from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Usuarios_Especiais
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import get_user_info

@app.route("/admin/usuario_especial", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios_especiais():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        if acao == "listar":
            Usuarios_Especiais_paginados = Usuarios_Especiais.query.paginate(page=page, per_page=10, error_out=False)
            extras['usuarios_especiais'] = Usuarios_Especiais_paginados.items
            extras['pagination'] = Usuarios_Especiais_paginados
        elif acao == 'procurar':
            pass
        return render_template("database/usuarios_especiais.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/usuarios_especiais.html", username=username, perm=perm, acao=acao, bloco=bloco)