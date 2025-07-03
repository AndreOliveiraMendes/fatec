from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Semestres
from auxiliar.decorators import admin_required

@app.route("/admin/semestres")
@admin_required
def gerenciar_semestres():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))