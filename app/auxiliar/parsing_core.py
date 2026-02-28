from datetime import datetime
from typing import Callable, Optional, TypeVar, overload

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