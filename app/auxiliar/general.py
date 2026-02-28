import enum
from typing import Any, Callable, Optional, TypeVar

V = TypeVar("V")

def formatar_valor(valor):
    if isinstance(valor, enum.Enum):
        return valor.value
    return valor

def dict_format(dictionary):
    campos = []
    for key in sorted(dictionary.keys()):
        campos.append(f"{key}: {dictionary[key]}")
    return "; ".join(campos)

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