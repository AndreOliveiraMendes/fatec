from flask import (Blueprint, redirect, render_template, send_from_directory,
                   session, url_for)

from app.auxiliar.auxiliar_routes import get_user_info

bp = Blueprint('default', __name__)

@bp.route("/")
def painel():
    return redirect(url_for('consultar_reservas.tela_televisor'))

@bp.route("/home")
def home():
    userid = session.get('userid')
    user = get_user_info(userid)
    return render_template("homepage.html", user=user)

@bp.route('/under_dev')
def under_dev_page():
    userid = session.get('userid')
    user = get_user_info(userid)
    return render_template('under_dev.html', user=user)

@bp.route('/favicon.svg')
def favicon_svg():
    return send_from_directory('static/images', 'favicon.svg')

@bp.route('/favicon.png')
def favicon_png():
    return send_from_directory('static/images', 'favicon.png')

@bp.route('/favicon.ico')
def favicon_ico():
    return send_from_directory('static/images', 'favicon.ico')

