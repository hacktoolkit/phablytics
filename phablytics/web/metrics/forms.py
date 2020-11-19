# Python Standard Library Imports
import datetime

# Third Party (PyPI) Imports
from flask import request
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    SelectField,
    validators,
)

# Phablytics Imports
from phablytics.metrics.constants import DATE_FORMAT_YMD
from phablytics.web.utils import format_choices


INTERVAL_OPTIONS = [
    'week',
    'month',
]


def get_filter_params():
    last_month_str = (datetime.date.today() - datetime.timedelta(days=31)).strftime(DATE_FORMAT_YMD)
    tomorrow_str = (datetime.date.today() + datetime.timedelta(days=1)).strftime(DATE_FORMAT_YMD)

    period_start = datetime.datetime.strptime(request.args.get('period_start', last_month_str), DATE_FORMAT_YMD)
    period_end = datetime.datetime.strptime(request.args.get('period_end', tomorrow_str), DATE_FORMAT_YMD)

    filter_params = {
        'interval': request.args.get('interval', INTERVAL_OPTIONS[0]),
        'period_start': period_start,
        'period_end': period_end,
    }
    return filter_params


class MetricsFilterForm(FlaskForm):
    interval = SelectField(
        label='Interval',
        choices=format_choices(INTERVAL_OPTIONS),
        validators=[
            validators.DataRequired(),
        ]
    )
    period_start = DateField(
        label='Period Start',
        format=DATE_FORMAT_YMD,
        render_kw={'placeholder': 'YYYY-MM-DD'},
        validators=[
            validators.DataRequired(),
        ]
    )
    period_end = DateField(
        label='Period End',
        format=DATE_FORMAT_YMD,
        render_kw={'placeholder': 'YYYY-MM-DD'},
        validators=[
            validators.DataRequired(),
        ]
    )
