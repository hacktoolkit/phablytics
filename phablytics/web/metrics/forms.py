# Python Standard Library Imports
import datetime

# Third Party (PyPI) Imports
from flask import request
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    SelectField,
    StringField,
    validators,
)

# Phablytics Imports
from phablytics.metrics.constants import (
    DATE_FORMAT_YMD,
    DEFAULT_INTERVAL_OPTION,
    INTERVAL_OPTIONS,
)
from phablytics.settings import PROJECT_TEAM_NAMES
from phablytics.utils import (
    end_of_month,
    end_of_quarter,
    get_active_usernames,
    get_customers,
    start_of_month,
    start_of_quarter,
)
from phablytics.web.utils import format_choices


# isort: off


def get_filter_params():
    """Returns a dictionary of form filter params for Metrics

    The result will be passed to `phablytics.metrics.metrics.Metrics::_retrieve_task_metrics()
    """
    interval = request.args.get('interval', DEFAULT_INTERVAL_OPTION)

    today = datetime.date.today()

    if interval == 'month':
        period_end_default = end_of_month(today)
        period_start_default = start_of_month(period_end_default - datetime.timedelta(days=360))
    elif interval == 'quarter':
        period_end_default = end_of_quarter(today)
        period_start_default = start_of_quarter(period_end_default - datetime.timedelta(days=360))
    else:
        # `interval == 'week'` or unspecified
        last_month = today - datetime.timedelta(days=31)
        tomorrow = today + datetime.timedelta(days=1)

        period_end_default = tomorrow
        period_start_default = last_month

    period_start = datetime.datetime.strptime(
        request.args.get(
            'period_start',
            period_start_default.strftime(DATE_FORMAT_YMD)
        ),
        DATE_FORMAT_YMD
    )
    period_end = datetime.datetime.strptime(
        request.args.get(
            'period_end',
            period_end_default.strftime(DATE_FORMAT_YMD)
        ),
        DATE_FORMAT_YMD
    )

    team = request.args.get('team', '')

    customer = request.args.get('customer', '')
    projects = request.args.get('projects', '')
    username = request.args.get('username', '')

    filter_params = {
        'interval': interval,
        'period_start': period_start,
        'period_end': period_end,
        'team': team,
        'customer': customer,
        'projects': projects,
        'username': username,
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
    team = SelectField(
        label='Team',
        choices=format_choices(
            PROJECT_TEAM_NAMES,
            include_blank=True
        )
    )
    customer = SelectField(
        label='Customer',
        choices=format_choices(
            sorted([
                customer.name
                for customer
                in get_customers()
            ]),
            include_blank=True
        )
    )
    projects = StringField()
    username = SelectField(
        label='User',
        choices=format_choices(
            get_active_usernames(),
            include_blank=True
        ),
    )
