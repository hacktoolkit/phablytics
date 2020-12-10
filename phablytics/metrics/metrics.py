# Python Standard Library Imports
import datetime
import pprint
from collections import namedtuple

# Third Party (PyPI) Imports
import numpy

# Phablytics Imports
from phablytics.constants import (
    MANIPHEST_STATUSES_CLOSED,
    MANIPHEST_STATUSES_OPEN,
)
from phablytics.metrics.constants import DATE_FORMAT_MDY_SHORT
from phablytics.metrics.stats import TaskMetricsStats
from phablytics.utils import (
    get_bulk_projects_by_name,
    get_customer_project,
    get_project_by_name,
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
            'points_added': self.points_added,
            'points_completed': self.points_completed,
            'ratio': self.ratio,
            'mean_days_to_resolution': self.mean_days_to_resolution,
        }
        return data

    ##
    # Raw Metrics

    @property
    def num_created(self):
        num_created = len(self.tasks_created)
        return num_created

    @property
    def num_closed(self):
        num_closed = len(self.tasks_closed)
        return num_closed

    @property
    def points_added(self):
        points = sum([task.points for task in self.tasks_created])
        return points

    @property
    def points_completed(self):
        points = sum([task.points for task in self.tasks_closed])
        return points

    ##
    # Ratio Metrics

    @property
    def ratio(self):
        try:
            ratio = self.num_closed / self.num_created
        except ZeroDivisionError:
            ratio = 1
        return ratio

    @property
    def num_created_per_total(self):
        rate = 1.0 * self.num_created / max(self.num_closed + self.num_created, 1)
        return rate

    @property
    def mean_days_to_resolution(self):
        values = [task.days_to_resolution for task in self.tasks_closed]
        mean_days = numpy.mean(values) if values else 0
        return mean_days

    ##
    # Normalized Metrics

    @property
    def days_to_resolution_per_point(self):
        days = sum([task.days_to_resolution for task in self.tasks_closed])
        days_per_story_point = 1.0 * days / max(self.points_completed, 1)
        return days_per_story_point

    @property
    def points_per_task(self):
        points_per_task = 1.0 * self.points_completed / max(self.num_closed, 1)
        return points_per_task

    @property
    def tasks_per_point(self):
        tasks_per_point = 1.0 * self.num_closed / max(self.points_completed, 1)
        return tasks_per_point


class AllTasksMetric(TaskMetric):
    """Tracks all tasks (any subtype) opened vs closed over time.
    """
    pass


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
    AllTasksMetric,
    BugMetric,
    FeatureMetric,
    StoryMetric,
    TaskMetric,
]

INTERVAL_DAYS_MAP = {
    'week': 7,
    'month': 30,
    'quarter': 90,
}
DEFAULT_INTERVAL_DAYS = INTERVAL_DAYS_MAP['week']


class Metrics:
    def _retrieve_task_metrics(
        self,
        interval,
        period_start,
        period_end,
        task_subtypes,
        team=None,
        customer=None,
        projects=None,
        *args,
        **kwargs
    ):
        now = datetime.datetime.now()

        task_metrics = []

        if period_start >= period_end:
            raise Exception('period_start must be before period_end')

        interval_days = INTERVAL_DAYS_MAP.get(interval, DEFAULT_INTERVAL_DAYS)

        if team:
            project = get_project_by_name(team, include_members=True)
            team_member_phids = project.member_phids
        else:
            team_member_phids = None

        project_phids = []

        if customer:
            customer_project = get_customer_project(customer)
            if customer_project:
                project_phids.append(customer_project.phid)
        else:
            pass

        if projects:
            project_names = projects.split(',')
            projects = get_bulk_projects_by_name(project_names)
            project_phids.extend([project.phid for project in projects])

        end = period_end

        # TODO: implement make_intervals(period_start, period_end, interval)
        while end > period_start:
            start = end - datetime.timedelta(days=interval_days)
            period_name = '{} to {}'.format(
                start.strftime(DATE_FORMAT_MDY_SHORT),
                end.strftime(DATE_FORMAT_MDY_SHORT)
            )

            tasks_created = get_tasks_created_over_period(
                start,
                end,
                subtypes=task_subtypes,
                author_phids=team_member_phids,
                project_phids=project_phids
            )
            tasks_closed = get_tasks_closed_over_period(
                start,
                end,
                subtypes=task_subtypes,
                closer_phids=team_member_phids,
                project_phids=project_phids
            )

            task_metric = TaskMetric(
                period_name=period_name,
                period_start=start,
                period_end=end,
                tasks_created=tasks_created,
                tasks_closed=tasks_closed
            )
            task_metrics.append(task_metric)

            end = start

        stats = TaskMetricsStats(task_metrics)

        return stats

    def alltasks(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of tasks opened/closed over a period
        """
        task_subtypes = [
            'bug',
            'default',
            'feature',
            'story',
        ]
        stats = self._retrieve_task_metrics(
            interval,
            period_start,
            period_end,
            task_subtypes,
            *args,
            **kwargs
        )
        return stats

    def bugs(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of bugs opened/closed over a period
        """
        task_subtypes = [
            'bug',
        ]
        stats = self._retrieve_task_metrics(
            interval,
            period_start,
            period_end,
            task_subtypes,
            *args,
            **kwargs
        )
        return stats

    def features(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of features opened/closed over a period
        """
        task_subtypes = [
            'feature',
        ]

        stats = self._retrieve_task_metrics(
            interval,
            period_start,
            period_end,
            task_subtypes,
            *args,
            **kwargs
        )
        return stats

    def stories(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of stories opened/closed over a period
        """
        task_subtypes = [
            'story',
        ]

        stats = self._retrieve_task_metrics(
            interval,
            period_start,
            period_end,
            task_subtypes,
            *args,
            **kwargs
        )
        return stats

    def tasks(self, interval, period_start, period_end, *args, **kwargs):
        """Returns the rate of tasks opened/closed over a period
        """
        task_subtypes = [
            'default',
        ]

        stats = self._retrieve_task_metrics(
            interval,
            period_start,
            period_end,
            task_subtypes,
            *args,
            **kwargs
        )
        return stats
