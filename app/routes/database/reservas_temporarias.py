from app.main import app
from flask import flash, session, render_template, request, redirect, url_for
from app.models import db
from app.auxiliar.decorators import admin_required

@app.route("/admin/reservas_temporarias")
@admin_required
def gerenciar_reservas_temporarias():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))