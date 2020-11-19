# Python Standard Library Imports
import datetime
import pprint
from collections import namedtuple

# Phablytics Imports
from phablytics.constants import (
    MANIPHEST_STATUSES_CLOSED,
    MANIPHEST_STATUSES_OPEN,
)
from phablytics.metrics.constants import DATE_FORMAT_MDY_SHORT
from phablytics.utils import (
    get_bugs_closed_over_period,
    get_bugs_created_over_period,
)


class MetricMeta(type):
    @property
    def name(cls):
        name = cls.__name__.replace('Metric', '') + 's'
        return name

    @property
    def slug(cls):
        slug = cls.name.lower()
        return slug

    @property
    def description(cls):
        desc = cls.__doc__
        return desc


class BugMetric(
    namedtuple('BugMetric', 'period_name,period_start,period_end,bugs_created,bugs_closed'),
    metaclass=MetricMeta
):
    """Tracks bugs opened vs closed over time.
    """
    def as_dict(self):
        data = {
            'period_name': self.period_name,
            'period_start': int(self.period_start.timestamp()),
            'period_end': int(self.period_end.timestamp()),
            'num_created': self.num_created,
            'num_closed': self.num_closed,
            'ratio': self.ratio,
        }
        return data

    @property
    def num_created(self):
        num_created = len(self.bugs_created)
        return num_created

    @property
    def num_closed(self):
        num_closed = len(self.bugs_closed)
        return num_closed

    @property
    def ratio(self):
        try:
            ratio = self.num_closed / self.num_created
        except ZeroDivisionError:
            ratio = 1
        return ratio


METRICS = [
    BugMetric,
]

INTERVAL_DAYS_MAP = {
    'week': 7,
    'month': 30,
}
DEFAULT_INTERVAL_DAYS = INTERVAL_DAYS_MAP['week']


class Metrics:
    def bugs(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of bugs opened/closed over a period
        """

        now = datetime.datetime.now()

        bug_metrics = []

        if period_start >= period_end:
            raise Exception('period_start must be before period_end')

        interval_days = INTERVAL_DAYS_MAP.get(interval, DEFAULT_INTERVAL_DAYS)

        end = period_end

        while end > period_start:
            start = end - datetime.timedelta(days=interval_days)
            period_name = '{} to {}'.format(
                start.strftime(DATE_FORMAT_MDY_SHORT),
                end.strftime(DATE_FORMAT_MDY_SHORT)
            )

            bugs_created = get_bugs_created_over_period(start, end)
            bugs_closed = get_bugs_closed_over_period(start, end)

            bug_metric = BugMetric(
                period_name=period_name,
                period_start=start,
                period_end=end,
                bugs_created=bugs_created,
                bugs_closed=bugs_closed
            )
            bug_metrics.append(bug_metric)

            end = start

        return bug_metrics
