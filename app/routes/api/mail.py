from flask import Blueprint, jsonify, request
from sqlalchemy import Select

from app.auxiliar.general import none_if_empty
from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Email


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