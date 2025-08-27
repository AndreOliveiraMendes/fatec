from flask import Blueprint, redirect, render_template, session, url_for

from app.auxiliar.auxiliar_routes import get_user_info

bp = Blueprint('default', __name__)

@bp.route("/")
def painel():
    return redirect(url_for('consultar_reservas.tela_televisor'))

@bp.route("/home")
def home():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("homepage.html", username=username, perm=perm)

@bp.route('/under_dev')
def under_dev_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template('under_dev.html', username=username, perm=perm)