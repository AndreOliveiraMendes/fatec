from flask import (Flask, abort, flash, jsonify, render_template, request,
                   session)
from werkzeug.exceptions import HTTPException

from app.auxiliar.auxiliar_routes import get_user_info
from config.general import SHOW_DEBUG_ERRORS
from config.mapeamentos import ERROR_MESSAGES, ERROR_TITLES


def wants_json_response():
    return request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html

def debug_message(e, code):
    if SHOW_DEBUG_ERRORS:
        flash(e, "danger")
    else:
        flash(ERROR_MESSAGES.get(code, "Ocorreu um erro inesperado."), "danger")

def handle_http_error(e: HTTPException):
    code = e.code or 500
    mensagem = getattr(e, 'description', e.name)

    userid = session.get('userid')
    user = get_user_info(userid)

    if wants_json_response():
        return jsonify({
            "error": e.name,
            "message": mensagem,
            "title": ERROR_TITLES.get(code, "Erro HTTP")
        }), code

    debug_message(e, code)
    return render_template(
        "http/http_error.html",
        user=user,
        message=mensagem,
        code=code,
        title=ERROR_TITLES.get(code, "Erro HTTP")
    ), code

def register_error_handler(app: Flask):
    for code in (400, 401, 403, 404, 409, 422, 500):
        app.register_error_handler(code, handle_http_error)