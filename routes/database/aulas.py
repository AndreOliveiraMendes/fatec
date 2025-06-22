from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Reservas_Fixas, Usuarios, Pessoas, Permissoes, Laboratorios, Aulas
from auxiliar.decorators import admin_required

@app.route("/admin/aulas")
@admin_required
def gerenciar_aulas():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('under_dev_page'))