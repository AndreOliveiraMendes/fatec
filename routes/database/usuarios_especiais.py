from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Cursos
from auxiliar.decorators import admin_required

@app.route("/admin/usuario_especial")
@admin_required
def gerenciar_usuarios_especiais():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))