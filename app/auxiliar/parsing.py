from datetime import date, datetime, time
from typing import Optional

from app.auxiliar.parsing_core import _parse_generic, _parse_generic_or_abort


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
    
def parse_time_string_or_abort(value: str | None, error_code, error_message, format: str | None = None) -> time:
    return _parse_generic_or_abort(
        value,
        format or "%H:%M",
        error_code,
        error_message,
        extractor=lambda dt: dt.time()
    )


def parse_date_string_or_abort(value: str | None, error_code, error_message, format: str | None = None) -> date:
    return _parse_generic_or_abort(
        value,
        error_code,
        error_message,
        format or "%Y-%m-%d",
        extractor=lambda dt: dt.date()
    )


def parse_datetime_string_or_abort(value: str | None, error_code, error_message, format: str | None = None) -> datetime:
    return _parse_generic_or_abort(
        value,
        error_code,
        error_message,
        format or "%Y-%m-%dT%H:%M"
    )