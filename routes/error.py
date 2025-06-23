from main import app
from flask import flash, session, request, jsonify, render_template
from auxiliar.auxiliar_routes import get_user_info

def wants_json_response():
    return request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html

@app.errorhandler(401)
def unauthorized_error(e):
    if wants_json_response():
        return jsonify({"error": "Unauthorized"}), 401
    flash(e, "danger")
    return render_template("http/401.html"), 401

@app.errorhandler(403)
def acesso_negado(e):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if wants_json_response():
        return jsonify({"error": "Access Denied", "user": username}), 403
    flash(e, "danger")
    return render_template("http/403.html", username=username, perm=perm), 403

@app.errorhandler(404)
def page_not_found(e):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if wants_json_response():
        return jsonify({"error": "Not Found"}), 404
    flash(e, "danger")
    return render_template('http/404.html', username=username, perm=perm), 404

@app.route('/under_dev')
def under_dev_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template('under_dev.html', username=username, perm=perm)