# Python Standard Library Imports
import datetime
import pprint
from collections import namedtuple

# Phablytics Imports
from phablytics.constants import (
    MANIPHEST_STATUSES_CLOSED,
    MANIPHEST_STATUSES_OPEN,
)
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
        ratio = self.num_closed / self.num_created
        return ratio


METRICS = [
    BugMetric,
]


class Metrics:
    def bugs(self, trailing_months=12):
        """Returns the rate of bugs opened/closed over the past N `trailing_months`
        """

        now = datetime.datetime.now()

        bug_metrics = []

        for i in range(trailing_months):
            period_name = f'{i * 30} to {(i + 1) * 30} days ago'
            period_end = now - datetime.timedelta(days=i * 30)
            period_start = period_end - datetime.timedelta(days=30)

            bugs_created = get_bugs_created_over_period(period_start, period_end)
            bugs_closed = get_bugs_closed_over_period(period_start, period_end)

            bug_metric = BugMetric(
                period_name=period_name,
                period_start=period_start,
                period_end=period_end,
                bugs_created=bugs_created,
                bugs_closed=bugs_closed
            )
            bug_metrics.append(bug_metric)

        return bug_metrics
