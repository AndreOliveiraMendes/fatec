from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from app.models import db, Reservas_Fixas
from app.auxiliar.decorators import admin_required

bp = Blueprint('reservas_fixas', __name__, url_prefix="/admin")

@bp.route("/reservas_fixa")
@admin_required
def gerenciar_reservas_fixas():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('error.under_dev_page'))