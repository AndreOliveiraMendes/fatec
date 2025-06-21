from main import app
from flask import flash, session, render_template
from auxiliar.auxiliar_routes import get_user_info

@app.errorhandler(403)
def acesso_negado(e):
    flash(e, "danger")
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("403.html", username=username, perm=perm), 403

@app.errorhandler(404)
def page_not_found(e):
    flash(e, "danger")
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template('404.html', username=username, perm=perm), 404

@app.route('/under_dev')
def under_dev_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template('under_dev.html', username=username, perm=perm)