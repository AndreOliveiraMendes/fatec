from flask import Blueprint, jsonify

from app.service.worker import worker_email_ativo

from .handler import definir_worker_email

bp = Blueprint("api_worker", __name__, url_prefix='/api/worker')

@bp.route("/status")
def worker_status():
    return jsonify({
        "ativo": worker_email_ativo()
    })

@bp.route("/start", methods=["POST"])
def worker_start():
    return jsonify({
        "ativo": definir_worker_email(True)
    })

@bp.route("/stop", methods=["POST"])
def worker_stop():
    return jsonify({
        "ativo": definir_worker_email(False)
    })

@bp.route("/toggle", methods=["POST"])
def worker_toggle():
    ativo = worker_email_ativo()

    return jsonify({
        "ativo": definir_worker_email(not ativo)
    })