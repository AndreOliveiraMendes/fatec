from flask import Blueprint

from app.decorators.decorators import admin_required
from config.json_related import load_mail_recipíents


bp = Blueprint('api_mail_recipient', __name__, url_prefix='/api/mail/recipient')

@bp.route("/list")
@admin_required
def api_mail_list():
    recipients = load_mail_recipíents()
    return {
        "recipients": recipients.get("recipients", [])
    }