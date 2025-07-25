from flask import Blueprint, session, render_template
from app.models import db, Usuarios
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import login_required

bp = Blueprint('default', __name__)

@bp.route("/")
def home():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("homepage.html", username=username, perm=perm)

@bp.route('/under_dev')
def under_dev_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template('under_dev.html', username=username, perm=perm)