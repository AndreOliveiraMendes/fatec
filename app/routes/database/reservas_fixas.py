import copy
from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from sqlalchemy.exc import IntegrityError
from config import PER_PAGE, AFTER_ACTION
from app.models import db, Reservas_Fixas
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, get_query_params, registrar_log_generico, get_session_or_request


bp = Blueprint('reservas_fixas', __name__, url_prefix="/database")

@bp.route("/reservas_fixa")
@admin_required
def gerenciar_reservas_fixas():
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('default.under_dev_page'))