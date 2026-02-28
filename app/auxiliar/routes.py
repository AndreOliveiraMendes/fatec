from datetime import date, timedelta
from typing import Any, MutableMapping, Optional, TypeVar

from flask import redirect, session, url_for
from flask.typing import ResponseReturnValue

from app.extensions import Base
from config.general import AFTER_ACTION
from config.mapeamentos import IGNORED_FORM_FIELDS



T = TypeVar("T", bound=Base)

def get_query_params(request):
    return {
        key: value
        for key, value in request.form.items()
        if key not in IGNORED_FORM_FIELDS
    }









def register_return(
    url: str,
    acao: str,
    extras: Optional[MutableMapping[str, Any]] = None,
    bloco: int = 0,
    **args: Any
) -> tuple[ResponseReturnValue | None, int | None]:

    if AFTER_ACTION == 'noredirect':
        if extras is not None:
            extras.update(args)
        return None, bloco

    if AFTER_ACTION in ['redirectabertura', 'redirectback']:
        if AFTER_ACTION == 'redirectback':
            session['acao'] = acao
        return redirect(url_for(url)), None

    raise ValueError(f"Configuração AFTER_ACTION inválida: {AFTER_ACTION}")

def time_range(start: date, end: date, step: int = 1):
    day = start
    while start <= day <= end:
        yield day
        day += timedelta(step)
