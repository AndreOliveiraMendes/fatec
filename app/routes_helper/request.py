from typing import List, Literal

from flask import Request, abort

from app.auxiliar.constant import Permission
from app.models.locais import Locais
from config.mapeamentos import IGNORED_FORM_FIELDS


def get_query_params(
    request: Request, 
    ignore_list: List[str] = None, 
    origin: Literal["form", "args"] = "form"
) -> dict:
    """
    Extract parameters from a request object, excluding specified fields.

    Parameters are retrieved from the request attribute specified by `origin` 
    ("form" or "args") and filtered to remove any keys in `ignore_list`. 
    By default, ignored fields include "page", "acao", and "bloco".

    Args:
        request: The request object containing parameters.
        ignore_list (List[str], optional): Keys to exclude from the result. 
            Defaults to None, in which case the default ignored fields are used.
        origin (Literal["form", "args"], optional): Attribute of `request` to use 
            ("form" or "args"). Defaults to "form".

    Returns:
        dict: Parameters from the request excluding the ignored fields.

    Raises:
        400 abort: If `origin` does not correspond to an attribute on `request`.

    Example:
        >>> get_query_params(request)
        {'name': 'Alice', 'email': 'alice@example.com'}
    """
    if ignore_list is None:
        ignore_list = IGNORED_FORM_FIELDS

    if not hasattr(request, origin):
        abort(400, description=f"Invalid origin '{origin}', must be an attribute of request.")
    
    source = getattr(request, origin)

    return {key: value for key, value in source.items() if key not in ignore_list}
    
def get_session_or_request(request, session, key, default=None):
    return session.pop(key, request.form.get(key, default))

def check_local(local: Locais, perm:Permission):
    if perm.has(Permission.ADMIN):
        return
    if local.disponibilidade.value == 'Indisponivel':
        abort(403, description="Local indisponível para reservas.")