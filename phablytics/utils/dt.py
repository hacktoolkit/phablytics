# Python Standard Library Imports
import calendar
import datetime


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


def start_of_month(dt):
    y, m, d = dt.year, dt.month, dt.day
    return datetime.date(y, m, calendar.monthrange(y, m)[0])


def end_of_month(dt):
    y, m, d = dt.year, dt.month, dt.day
    return datetime.date(y, m, calendar.monthrange(y, m)[1])
