from functools import wraps

from flask import abort, g, request, session

from app.auxiliar.constant import Permission
from app.dao.internal.usuarios import get_user
from app.extensions import db
from app.models.usuarios import Permissoes
from app.routes_helper.request import get_session_or_request
from config.database_views import get_url


def require_login():
    userid = session.get('userid')
    if not userid:
        abort(401, description="Usuário não autenticado.")
    return userid

def require_permission(flag):
    userid = require_login()
    perm = db.session.get(Permissoes, userid)
    if not perm or not (perm.permissao & flag):
        abort(403, description="Usuário não possui permissão necessária.")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_login()
        return f(*args, **kwargs)
    return decorated_function

def reserva_fixa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(Permission.RESERVA_FIXA)
        return f(*args, **kwargs)
    return decorated_function

def reserva_temp_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(Permission.RESERVA_TEMPORARIA)
        return f(*args, **kwargs)
    return decorated_function

def reserva_auditorio_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(Permission.RESERVA_AUDITORIO)
        return f(*args, **kwargs)
    return decorated_function

def reserva_equipamento_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(Permission.RESERVA_EQUIPAMENTO)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(Permission.ADMIN)
        return f(*args, **kwargs)
    return decorated_function

def cmd_config_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(Permission.CMD_CONFIG)
        return f(*args, **kwargs)
    return decorated_function

def crud_route(default_acao="abertura"):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            blueprint = request.blueprint
            assert blueprint is not None

            g.url = get_url(blueprint)
            
            g.redirect_action = None

            g.acao = get_session_or_request(
                request, session, 'acao', default_acao
            )

            g.bloco = int(request.form.get('bloco', 0))
            g.page = int(request.form.get('page', 1))

            g.userid = session.get('userid')
            g.user = get_user(g.userid)

            g.extras = {'url': g.url}

            return f(*args, **kwargs)

        return wrapper
    return decorator

def register_handler(handler, acao, bloco):
    def decorator(func):
        handler[(acao, bloco)] = func
        return func
    return decorator