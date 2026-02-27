from datetime import date, datetime, time


def parse_time(time:time):
    return time.strftime('%H:%M') if time else None

def parse_date(date:date):
    return date.strftime('%d/%m/%Y') if date else None

def parse_datetime(datetime:datetime):
    return datetime.strftime('%d/%m/%Y %H:%M') if datetime else None