
from flask import abort

from app.auxiliar.constant import Permission
from app.models.locais import Locais
from config.mapeamentos import IGNORED_FORM_FIELDS


def get_query_params(request):
    return {
        key: value
        for key, value in request.form.items()
        if key not in IGNORED_FORM_FIELDS
    }
    
def get_session_or_request(request, session, key, default=None):
    return session.pop(key, request.form.get(key, default))

def check_local(local: Locais, perm):
    if perm & Permission.ADMIN > 0:
        return
    if local.disponibilidade.value == 'Indisponivel':
        abort(403, description="Local indisponível para reservas.")