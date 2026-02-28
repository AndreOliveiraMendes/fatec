from typing import Any, MutableMapping, Optional

from flask import redirect, session, url_for
from flask.typing import ResponseReturnValue

from config.general import AFTER_ACTION


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


