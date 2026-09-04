from flask import Blueprint, jsonify

from app.decorators.decorators import admin_required
from app.service.worker import worker_email_ativo

from .handler import check_worker_heartbeat, definir_worker_email

bp = Blueprint("api_worker", __name__, url_prefix='/api/worker')

@bp.route("/status")
def worker_status():
    return jsonify({
        "ativo": worker_email_ativo(),
        "heartbeat": check_worker_heartbeat()
    })

@admin_required
@bp.route("/start", methods=["POST"])
def worker_start():
    code, error, ativo = definir_worker_email(True)
    if code != 200:
        return jsonify({
            "ativo": ativo,
            "error": str(error)
        }), code
    return jsonify({
        "ativo": ativo
    })

@admin_required
@bp.route("/stop", methods=["POST"])
def worker_stop():
    code, error, ativo = definir_worker_email(False)
    if code != 200:
        return jsonify({
            "ativo": ativo,
            "error": str(error)
        }), code
    return jsonify({
        "ativo": ativo
    })

@admin_required
@bp.route("/toggle", methods=["POST"])
def worker_toggle():
    code, error, ativo = definir_worker_email(not worker_email_ativo())
    if code != 200:
        return jsonify({
            "ativo": ativo,
            "error": str(error)
        }), code
    return jsonify({
        "ativo": ativo
    })