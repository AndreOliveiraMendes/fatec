from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Reservas_Fixa, Usuarios, Pessoas, Usuarios_Permissao, Laboratorios, Aulas
from decorators import admin_required

@app.route("/admin/usuarios", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            usuarios = Usuarios.query.all()
            extras['usarios'] = usuarios
        return render_template("database/usuarios.html", acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/usuarios.html", acao=acao, bloco=bloco)