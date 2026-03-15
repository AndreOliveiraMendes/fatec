from datetime import datetime
from typing import Callable, Optional, TypeVar, overload

from flask import abort

S = TypeVar("S")

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
    
@overload
def _parse_generic_or_abort(
    value: str | None,
    format: str,
    error_code: int,
    error_message: str,
    extractor: Callable[[datetime], S]
) -> S: ...
@overload
def _parse_generic_or_abort(
    value: str | None,
    format: str,
    error_code: int,
    error_message: str,
    extractor: None = None
) -> datetime: ...

def _parse_generic_or_abort(
    value: str | None,
    format: str,
    error_code: int,
    error_message: str,
    extractor: Callable[[datetime], S] | None = None
) -> S | datetime:
    if not value:
        abort(error_code, description=error_message)
    try:
        dt = datetime.strptime(value, format)
        return extractor(dt) if extractor else dt
    except ValueError:
        abort(error_code, description=error_message)