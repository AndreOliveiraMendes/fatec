from flask import Blueprint, jsonify, request

from .handler.handler_select import get_results

bp = Blueprint('api_select', __name__, url_prefix='/api/')

@bp.route("/select/<entity>")
def select(entity):

    q = request.args.get("q")
    
    result, code = get_results(entity, q)

    return jsonify(result), code