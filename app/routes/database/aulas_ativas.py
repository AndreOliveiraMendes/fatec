from app.main import app
from flask import flash, session, render_template, request, redirect, url_for
from app.models import db, Aulas_Ativas
from app.auxiliar.decorators import admin_required

@app.route("/admin/aulas_ativas", methods=["GET", "POST"])
@admin_required
def gerenciar_aulas_ativas():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))