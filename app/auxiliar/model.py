from datetime import date, datetime, time
from typing import Optional


def parse_time(time:Optional[time]):
    return time.strftime('%H:%M') if time else None

def parse_date(date:Optional[date]):
    return date.strftime('%d/%m/%Y') if date else None

def parse_datetime(datetime:Optional[datetime]):
    return datetime.strftime('%d/%m/%Y %H:%M') if datetime else None