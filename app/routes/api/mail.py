from flask import Blueprint, jsonify, request, url_for
from sqlalchemy import Select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import none_if_empty
from app.enums import StatusEmailEnum
from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Email
from app.routes.reserva_fixa.handlers import _handle_db_error

bp = Blueprint("api_mail", __name__, url_prefix='/api/mail/self')


@bp.route("/list")
def list():
    res_aud = none_if_empty(request.args.get('id_reserva'), int)

    filters = []
    if res_aud is not None:
        filters.append(Reserva_Auditorio_Email.id_reserva_auditorio == res_aud)

    sel_mail = Select(Reserva_Auditorio_Email)
    if filters:
        sel_mail = sel_mail.where(*filters)

    emails = db.session.execute(sel_mail).scalars().all()

    return jsonify([email.to_dict() for email in emails])

@bp.route("/content/<int:id_email>")
def get_content(id_email):
    email = db.session.get(
        Reserva_Auditorio_Email,
        id_email
    )

    if email is None:
        return jsonify({
            "error": "Email não encontrado"
        }), 404

    return jsonify({
        "id": email.id_email,
        "destinatario": email.destinatario,
        "assunto": email.assunto,
        "conteudo": email.corpo_email,
        "status": email.status_envio.value,
        "ultima_tentativa": (
            email.ultima_tentativa.isoformat()
            if email.ultima_tentativa
            else None
        ),
        "url_envio": url_for(
            "api_mail.mark_to_be_send",
            id_email=email.id_email
        )
    })

@bp.route("/<int:id_email>/mark-to-be-send", methods=["POST"])
def mark_to_be_send(id_email):
    email = db.session.get(
        Reserva_Auditorio_Email,
        id_email
    )

    if email is None:
        return jsonify({
            "error": "Email não encontrado"
        }), 404

    try:
        email.status_envio = StatusEmailEnum.PENDENTE

        db.session.add(email)

        db.session.commit()
    except DB_ERRORS as e:
        _handle_db_error(e, "Erro ao marcar email para envio")

    return jsonify({
        "success": True
    })