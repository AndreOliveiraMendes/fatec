from functools import wraps

from flask import abort, session

from app.auxiliar.constant import Permission
from app.extensions import db
from app.models.usuarios import Permissoes


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