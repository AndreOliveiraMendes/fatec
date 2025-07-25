from flask import flash, session, request, jsonify, render_template
from app.auxiliar.auxiliar_routes import get_user_info
from config.general import SHOW_DEBUG_ERRORS

ERROR_MESSAGES = {
    400: "Requisição inválida",
    401: "Você precisa fazer login para acessar esta página.",
    403: "Você não possui as permissões necessárias para acessar esta página.",
    404: "A página requisitada não existe.",
    422: "Entidade não processável."
}

def wants_json_response():
    return request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html

def debug_message(e, code):
    if SHOW_DEBUG_ERRORS:
        flash(e, "danger")
    else:
        flash(ERROR_MESSAGES.get(code, "Ocorreu um erro inesperado."), "danger")

def register_error_handler(app):
    @app.errorhandler(400)
    def bad_request_error(e):
        userid = session.get('userid')
        username, perm = get_user_info(userid)
        mensagem = getattr(e, 'description', 'Bad Request')
        if wants_json_response():
            return jsonify({"error": "Bad Request"}), 400
        debug_message(e, 400)
        return render_template("http/400.html", username=username, perm=perm, message=mensagem), 400

    @app.errorhandler(401)
    def unauthorized_error(e):
        if wants_json_response():
            return jsonify({"error": "Unauthorized"}), 401
        debug_message(e, 401)
        return render_template("http/401.html"), 401

    @app.errorhandler(403)
    def acesso_negado(e):
        userid = session.get('userid')
        username, perm = get_user_info(userid)
        mensagem = getattr(e, 'description', 'Access Denied')
        if wants_json_response():
            return jsonify({"error": "Access Denied", "message": mensagem, "user": username, "perm": perm}), 403
        debug_message(e, 403)
        return render_template("http/403.html", username=username, perm=perm, message=mensagem), 403

    @app.errorhandler(404)
    def page_not_found(e):
        userid = session.get('userid')
        username, perm = get_user_info(userid)
        if wants_json_response():
            return jsonify({"error": "Not Found"}), 404
        debug_message(e, 404)
        return render_template('http/404.html', username=username, perm=perm), 404
    
    @app.errorhandler(422)
    def unprocessable_entity(e):
        userid = session.get('userid')
        username, perm = get_user_info(userid)
        mensagem = getattr(e, 'description', 'Unprocessable Entity')
        if wants_json_response():
            return jsonify({"error": "Unprocessable Entity"}), 422
        debug_message(e, 422)
        return render_template('http/422.html', username=username, perm=perm, mensagem=mensagem), 422