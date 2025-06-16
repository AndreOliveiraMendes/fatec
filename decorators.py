from functools import wraps
from flask import session, redirect, url_for, abort

PERM_RESERVA_FIXA = 1
PERM_RESERVA_TEMP = 2
PERM_ADMIN = 4

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'userid' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def reserva_fixa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models import Usuarios_Permissao  # ou onde estiver
        userid = session.get('userid')
        if not userid:
            return redirect(url_for('login'))

        perm = Usuarios_Permissao.query.filter_by(id_permissao_usuario=userid).first()
        if not perm or not (perm.permissao & PERM_RESERVA_FIXA):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def reserva_temp_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models import Usuarios_Permissao  # ou onde estiver
        userid = session.get('userid')
        if not userid:
            return redirect(url_for('login'))

        perm = Usuarios_Permissao.query.filter_by(id_permissao_usuario=userid).first()
        if not perm or not (perm.permissao & PERM_RESERVA_TEMP):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models import Usuarios_Permissao  # ou onde estiver
        userid = session.get('userid')
        if not userid:
            return redirect(url_for('login'))

        perm = Usuarios_Permissao.query.filter_by(id_permissao_usuario=userid).first()
        if not perm or not (perm.permissao & PERM_ADMIN):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function