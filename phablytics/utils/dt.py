# Python Standard Library Imports
import calendar
import datetime
import math
import time
import typing as T


def hours_ago(ts: T.Optional[int] = None) -> T.Optional[int]:
    """Returns the number of hours ago `ts` represents

    Rounds up to the nearest whole hour
    """
    if ts is None:
        hours = None
    else:
        now = time.time()
        if ts > now:
            raise Exception('Cannot compute hours ago for timestamp in the future')

        d_seconds = math.ceil(now - ts)
        td = datetime.timedelta(seconds=d_seconds)
        hours = td.days * 24 + math.ceil(td.seconds / 3600)

    return hours


def start_of_quarter(dt):
    y, m, d = dt.year, dt.month, dt.day

    quarter_starts = (
        datetime.date(y, 1, 1),
        datetime.date(y, 4, 1),
        datetime.date(y, 7, 1),
        datetime.date(y, 10, 1),
    )

    for soq in quarter_starts:
        if soq < dt:
            start_of_quarter = soq

    return start_of_quarter


def end_of_quarter(dt):
    y, m, d = dt.year, dt.month, dt.day

    quarter_ends = (
        datetime.date(y, 3, 31),
        datetime.date(y, 6, 30),
        datetime.date(y, 9, 30),
        datetime.date(y, 12, 31),
    )

    for eoq in quarter_ends:
        if eoq > dt:
            end_of_quarter = eoq

    return end_of_quarter


def start_of_month(dt: datetime.datetime):
    """Returns the first day of the month for `dt`.
    """
    y, m, d = dt.year, dt.month, dt.day
    return datetime.date(y, m, 1)


def end_of_month(dt: datetime.datetime):
    """Returns the last day of the month for `dt`.
    """
    y, m, d = dt.year, dt.month, dt.day
    return datetime.date(y, m, calendar.monthrange(y, m)[1])
