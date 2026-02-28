from datetime import date, timedelta


def time_range(start: date, end: date, step: int = 1):
    day = start
    while start <= day <= end:
        yield day
        day += timedelta(step)