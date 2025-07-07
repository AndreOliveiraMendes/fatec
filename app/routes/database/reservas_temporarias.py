from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from app.models import db
from app.auxiliar.decorators import admin_required

bp = Blueprint('reservas_temporarias', __name__, url_prefix="/admin")

@bp.route("/reservas_temporarias")
@admin_required
def gerenciar_reservas_temporarias():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('error.under_dev_page'))