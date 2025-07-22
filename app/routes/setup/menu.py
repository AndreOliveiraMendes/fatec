from flask import Blueprint, session, render_template
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import admin_required

bp = Blueprint('setup', __name__, url_prefix="/database/fast_setup/")

@bp.route("/menu")
@admin_required
def fast_setup_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)

    return render_template('database/setup/menu.html', username=username, perm=perm)