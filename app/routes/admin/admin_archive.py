from flask import Blueprint, jsonify, render_template, request, session

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.routes.admin.handlers.handler_admin_archive import (
    archive_all_previous_years, archive_by_semestre, download_archive,
    list_archives_files, preview_all_previous_years, preview_semestre)

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
    result = archive_all_previous_years()
    return jsonify({"message": result})

@bp.route("/preview/semestre", methods=["POST"])
@admin_required
def preview_semestre_route():
    result = preview_semestre()
    return jsonify({"message": result})


@bp.route("/preview/ano", methods=["POST"])
@admin_required
def preview_ano_route():
    result = preview_all_previous_years()
    return jsonify({"message": result})

@bp.route("/list", methods=["POST"])
@admin_required
def list_archives():
    result = list_archives_files()
    return jsonify({"files": result})

@bp.route("/download", methods=["GET"])
@admin_required
def donwload_all_archives():
    tipo = request.args.get("tipo")
    file = request.args.get("file")
    return download_archive(tipo, file)