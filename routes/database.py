from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Reservas_Fixa, Usuarios, Usuarios_Permissao, Laboratorios, Aulas
from decorators import login_required, admin_required

@app.route("/admin/usuarios")
@admin_required
def gerenciar_usuarios():
    acao = request.form.get('acao', 'abertura')
    return render_template("database/usuarios.html", acao=acao)

@app.route("/admin/usuario_especial")
@admin_required
def gerenciar_usuario_especial():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))

@app.route("/admin/aulas")
@admin_required
def gerenciar_aulas():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))

@app.route("/admin/laboratorios")
@admin_required
def gerenciar_laboratorios():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))

@app.route("/admin/reservas_fixa")
@admin_required
def gerenciar_reservas_fixa():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))

@app.route("/admin/permissoes")
@admin_required
def gerenciar_permissoes():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))