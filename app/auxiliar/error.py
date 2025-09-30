from flask import Flask, flash, jsonify, render_template, request, session

from app.auxiliar.auxiliar_routes import get_user_info
from config.general import SHOW_DEBUG_ERRORS
from config.mapeamentos import ERROR_MESSAGES


def wants_json_response():
    return request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html

def debug_message(e, code):
    if SHOW_DEBUG_ERRORS:
        flash(e, "danger")
    else:
        flash(ERROR_MESSAGES.get(code, "Ocorreu um erro inesperado."), "danger")

def register_error_handler(app:Flask):
    @app.errorhandler(400)
    def bad_request_error(e):
        userid = session.get('userid')
        user = get_user_info(userid)
        mensagem = getattr(e, 'description', 'Bad Request')
        if wants_json_response():
            return jsonify({"error": "Bad Request"}), 400
        debug_message(e, 400)
        return render_template("http/400.html", user=user, message=mensagem), 400

    @app.errorhandler(401)
    def unauthorized_error(e):
        if wants_json_response():
            return jsonify({"error": "Unauthorized"}), 401
        debug_message(e, 401)
        return render_template("http/401.html"), 401

    @app.errorhandler(403)
    def acesso_negado(e):
        userid = session.get('userid')
        user = get_user_info(userid)
        mensagem = getattr(e, 'description', 'Access Denied')
        if wants_json_response():
            return jsonify({"error": "Access Denied", "message": mensagem, "user": user.username, "perm": user.perm}), 403
        debug_message(e, 403)
        return render_template("http/403.html", user=user, message=mensagem), 403

    @app.errorhandler(404)
    def page_not_found(e):
        userid = session.get('userid')
        user = get_user_info(userid)
        if wants_json_response():
            return jsonify({"error": "Not Found"}), 404
        debug_message(e, 404)
        return render_template('http/404.html', user=user), 404

    @app.errorhandler(409)
    def conflict(e):
        userid = session.get('userid')
        user = get_user_info(userid)
        mensagem = getattr(e, 'description', 'Conflict ')
        if wants_json_response():
            return jsonify({"error": "Conflict"}), 409
        debug_message(e, 409)
        return render_template('http/409.html', user=user), 409

    @app.errorhandler(422)
    def unprocessable_entity(e):
        userid = session.get('userid')
        user = get_user_info(userid)
        mensagem = getattr(e, 'description', 'Unprocessable Entity')
        if wants_json_response():
            return jsonify({"error": "Unprocessable Entity"}), 422
        debug_message(e, 422)
        return render_template('http/422.html', user=user, mensagem=mensagem), 422

    @app.errorhandler(500)
    def internal_server_error(e):
        userid = session.get('userid')
        user = get_user_info(userid)
        if wants_json_response():
            return jsonify({"error": "Internal Server Error"}), 500
        debug_message(e, 500)
        return render_template('http/500.html', user=user), 500