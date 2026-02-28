import enum
from datetime import date, datetime, time
from typing import Any, Callable, Optional, TypeVar, overload







        
def _friendly_db_message(error):
    raw = str(getattr(error, "orig", error)).lower()

    if "duplicate entry" in raw or "unique constraint" in raw:
        return "Registro já existe."

    if "foreign key" in raw:
        return "Registro relacionado não encontrado."

    if "cannot be null" in raw or "not null constraint" in raw:
        return "Campo obrigatório não preenchido."

    if "data too long" in raw:
        return "Valor maior que o permitido."

    return "Erro ao salvar dados."
