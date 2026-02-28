import enum
from datetime import date, datetime, time
from typing import Any, Callable, Optional, TypeVar, overload



V = TypeVar("V")
S = TypeVar("S")

def formatar_valor(valor):
    if isinstance(valor, enum.Enum):
        return valor.value
    return valor

def dict_format(dictionary):
    campos = []
    for key in sorted(dictionary.keys()):
        campos.append(f"{key}: {dictionary[key]}")
    return "; ".join(campos)
        
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

def none_if_empty(value: Any, cast_type: Callable[[Any], V] = str) -> Optional[V]:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    try:
        return cast_type(value)
    except (ValueError, TypeError):
        return None
    
@overload
def _parse_generic(
    value: str | None,
    format: str,
    extractor: Callable[[datetime], S]
) -> S | None: ...
@overload
def _parse_generic(
    value: str | None,
    format: str,
    extractor: None = None
) -> datetime | None: ...

def _parse_generic(
    value: str | None,
    format: str,
    extractor: Callable[[datetime], S] | None = None
) -> Optional[S | datetime]:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, format)
        return extractor(dt) if extractor else dt
    except ValueError:
        return None

def parse_time_string(value: str | None, format: str | None = None) -> Optional[time]:
    return _parse_generic(
        value,
        format or "%H:%M",
        extractor=lambda dt: dt.time()
    )


def parse_date_string(value: str | None, format: str | None = None) -> Optional[date]:
    return _parse_generic(
        value,
        format or "%Y-%m-%d",
        extractor=lambda dt: dt.date()
    )


def parse_datetime_string(value: str | None, format: str | None = None) -> Optional[datetime]:
    return _parse_generic(
        value,
        format or "%Y-%m-%dT%H:%M"
    )