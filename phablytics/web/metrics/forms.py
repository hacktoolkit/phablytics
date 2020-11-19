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
from phablytics.settings import PROJECT_TEAM_NAMES
from phablytics.web.utils import format_choices


INTERVAL_OPTIONS = [
    'week',
    'month',
]


def get_filter_params():
    interval = request.args.get('interval', INTERVAL_OPTIONS[0])

    last_month_str = (datetime.date.today() - datetime.timedelta(days=31)).strftime(DATE_FORMAT_YMD)
    tomorrow_str = (datetime.date.today() + datetime.timedelta(days=1)).strftime(DATE_FORMAT_YMD)

    period_start = datetime.datetime.strptime(request.args.get('period_start', last_month_str), DATE_FORMAT_YMD)
    period_end = datetime.datetime.strptime(request.args.get('period_end', tomorrow_str), DATE_FORMAT_YMD)

    team = request.args.get('team', '')

    filter_params = {
        'interval': interval,
        'period_start': period_start,
        'period_end': period_end,
        'team': team,
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
    # projects = StringField
    team = SelectField(
        label='Team',
        choices=format_choices(PROJECT_TEAM_NAMES, include_blank=True)
    )
