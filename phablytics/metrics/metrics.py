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
    get_tasks_closed_over_period,
    get_tasks_created_over_period,
    pluralize,
)


class MetricMeta(type):
    @property
    def name(cls):
        metric_type = cls.__name__.replace('Metric', '')
        name = pluralize(metric_type)
        return name

    @property
    def slug(cls):
        slug = cls.name.lower()
        return slug

    @property
    def description(cls):
        desc = cls.__doc__
        return desc


class TaskMetric(
    namedtuple('TaskMetric', 'period_name,period_start,period_end,tasks_created,tasks_closed'),
    metaclass=MetricMeta
):
    """Tracks tasks opened vs closed over time.
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
        num_created = len(self.tasks_created)
        return num_created

    @property
    def num_closed(self):
        num_closed = len(self.tasks_closed)
        return num_closed

    @property
    def ratio(self):
        try:
            ratio = self.num_closed / self.num_created
        except ZeroDivisionError:
            ratio = 1
        return ratio


class BugMetric(TaskMetric):
    """Tracks bugs opened vs closed over time.
    """
    pass


class FeatureMetric(TaskMetric):
    """Tracks features opened vs closed over time.
    """
    pass


class StoryMetric(TaskMetric):
    """Tracks stories opened vs closed over time.
    """
    pass


METRICS = [
    BugMetric,
    FeatureMetric,
    StoryMetric,
    TaskMetric,
]

INTERVAL_DAYS_MAP = {
    'week': 7,
    'month': 30,
}
DEFAULT_INTERVAL_DAYS = INTERVAL_DAYS_MAP['week']


class Metrics:
    def _retrieve_task_metrics(
        self,
        interval,
        period_start,
        period_end,
        task_subtypes
    ):
        now = datetime.datetime.now()

        task_metrics = []

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

            tasks_created = get_tasks_created_over_period(start, end, subtypes=task_subtypes)
            tasks_closed = get_tasks_closed_over_period(start, end, subtypes=task_subtypes)

            task_metric = TaskMetric(
                period_name=period_name,
                period_start=start,
                period_end=end,
                tasks_created=tasks_created,
                tasks_closed=tasks_closed
            )
            task_metrics.append(task_metric)

            end = start

        return task_metrics

    def bugs(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of bugs opened/closed over a period
        """
        task_subtypes = [
            'bug',
        ]
        task_metrics = self._retrieve_task_metrics(
            interval,
            period_start,
            period_end,
            task_subtypes
        )
        return task_metrics

    def features(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of features opened/closed over a period
        """
        task_subtypes = [
            'feature',
        ]

        task_metrics = self._retrieve_task_metrics(
            interval,
            period_start,
            period_end,
            task_subtypes
        )
        return task_metrics

    def stories(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of stories opened/closed over a period
        """
        task_subtypes = [
            'story',
        ]

        task_metrics = self._retrieve_task_metrics(
            interval,
            period_start,
            period_end,
            task_subtypes
        )
        return task_metrics

    def tasks(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of tasks opened/closed over a period
        """
        task_subtypes = [
            'default',
        ]

        task_metrics = self._retrieve_task_metrics(
            interval,
            period_start,
            period_end,
            task_subtypes
        )
        return task_metrics
