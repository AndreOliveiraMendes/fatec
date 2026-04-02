from flask import Blueprint, jsonify, render_template, session

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.routes.admin.handlers.handler_admin_archive import archive_by_semestre, archive_last_year_historicos, preview_last_year, preview_semestre

bp = Blueprint("admin_archive", __name__, url_prefix='/admin/archive')

@bp.route("/menu")
@admin_required
def menu():
    user = get_user(session.get('userid'))

    return render_template("admin/archive/menu.html", user=user)

@bp.route("/semestre", methods=["POST"])
@admin_required
def archive_semestre():
    result = archive_by_semestre()

    return jsonify({"message": result})

@bp.route("/ano", methods=["POST"])
@admin_required
def archive_ano():
    result = archive_last_year_historicos()
    return jsonify({"message": result})

@bp.route("/preview/semestre", methods=["POST"])
@admin_required
def preview_semestre_route():
    result = preview_semestre()
    return jsonify({"message": result})


@bp.route("/preview/ano", methods=["POST"])
@admin_required
def preview_ano_route():
    result = preview_last_year()
    return jsonify({"message": result})