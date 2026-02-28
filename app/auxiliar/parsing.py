from datetime import date, datetime, time
from typing import Optional

from app.auxiliar.parsing_core import _parse_generic


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