from functools import wraps

from flask import abort, session

from app.auxiliar.constant import (PERM_ADMIN, PERM_RESERVA_AUDITORIO,
                                   PERM_RESERVA_FIXA, PERM_RESERVA_TEMPORARIA)
from app.models import Permissoes, db


def require_login():
    userid = session.get('userid')
    if not userid:
        abort(401)
    return userid

def require_permission(flag):
    userid = require_login()
    perm = db.session.get(Permissoes, userid)
    if not perm or not (perm.permissao & flag):
        abort(403)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_login()
        return f(*args, **kwargs)
    return decorated_function

def reserva_fixa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(PERM_RESERVA_FIXA)
        return f(*args, **kwargs)
    return decorated_function

def reserva_temp_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(PERM_RESERVA_TEMPORARIA)
        return f(*args, **kwargs)
    return decorated_function

def reserva_auditorio_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(PERM_RESERVA_AUDITORIO)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        require_permission(PERM_ADMIN)
        return f(*args, **kwargs)
    return decorated_function