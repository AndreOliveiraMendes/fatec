from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from app.models import db, Aulas_Ativas
from app.auxiliar.decorators import admin_required

bp = Blueprint('aulas_ativas', __name__, url_prefix="/admin")

@bp.route("/aulas_ativas", methods=["GET", "POST"])
@admin_required
def gerenciar_aulas_ativas():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('error.under_dev_page'))