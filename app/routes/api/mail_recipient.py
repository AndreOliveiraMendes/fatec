from flask import Blueprint, request

from app.decorators.decorators import admin_required
from app.routes.api.handler.handler_mail_config import same_recipient
from config.json_related import load_mail_recipíents, savel_mail_recipients

bp = Blueprint('api_mail_recipient', __name__, url_prefix='/api/mail/recipient')

@bp.route("/list")
@admin_required
def api_mail_list():
    recipients = load_mail_recipíents()
    return {
        "recipients": recipients
    }

@bp.route("/save", methods=["POST"])
@admin_required
def api_mail_save():
    data = request.get_json()
    recipients = load_mail_recipíents()
    if not data:
        return {"error": "No data provided"}, 400
    if data.get("id"):
        try:
            data['id'] = int(data['id'])
        except ValueError:
            return {"error": "Invalid ID format"}, 400
    existing_recipient = next((recipient for recipient in recipients if same_recipient(recipient, data, data.get("id") is not None)), None)

    if existing_recipient:
        data["id"] = existing_recipient["id"]

        existing_recipient.update(data)
    else:
        new_id = max((recipient["id"] for recipient in recipients), default=0)
        data["id"] = new_id + 1
        recipients.append(data)
    savel_mail_recipients(recipients)
    return {"success": True}