from flask import Blueprint, jsonify

from app.extensions import db
from app.service.worker import worker_email_ativo
from app.models.config import Configuracoes


bp = Blueprint("api_worker", __name__, url_prefix='/api/worker')

@bp.route("/status")
def worker_status():
    return jsonify({
        "ativo": worker_email_ativo()
    })

@bp.route("/toggle", methods=["POST"])
def worker_toggle():
    config = db.session.get(
        Configuracoes,
        "worker_email_ativo"
    )

    if config is None:
        config = Configuracoes(
            chave="worker_email_ativo",
            valor="true"
        )
        db.session.add(config)

    config.valor = (
        "false"
        if config.valor.lower() == "true"
        else "true"
    )

    db.session.commit()

    return jsonify({
        "ativo": config.valor == "true"
    })

@bp.route("/start", methods=["POST"])
def worker_start():
    config = db.session.get(
        Configuracoes,
        "worker_email_ativo"
    )

    if config is None:
        config = Configuracoes(
            chave="worker_email_ativo",
            valor="true"
        )
        db.session.add(config)
    else:
        config.valor = "true"

    db.session.commit()

    return jsonify({
        "ativo": True
    })

@bp.route("/stop", methods=["POST"])
def worker_stop():
    config = db.session.get(
        Configuracoes,
        "worker_email_ativo"
    )

    if config is None:
        config = Configuracoes(
            chave="worker_email_ativo",
            valor="false"
        )
        db.session.add(config)
    else:
        config.valor = "false"

    db.session.commit()

    return jsonify({
        "ativo": False
    })