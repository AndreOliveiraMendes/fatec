from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Historicos
from auxiliar.decorators import admin_required

@app.route("/admin/historico", methods=["GET", "POST"])
@admin_required
def gerenciar_Historico():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))