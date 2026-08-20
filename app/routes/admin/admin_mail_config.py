from flask import Blueprint, render_template, session

from app.dao.internal.usuarios import get_user

bp = Blueprint('admin_mail_config', __name__, url_prefix='/manage_mail_config')

@bp.route("/settings")
def manage_mail_config():
    userid = session.get('userid')
    user = get_user(userid)
    return render_template("admin/mail/mail_config.html", user=user)

@bp.route("/destinatario")
def manage_mail_destinatario():
    userid = session.get('userid')
    user = get_user(userid)
    return render_template("admin/mail/destinatario.html", user=user)