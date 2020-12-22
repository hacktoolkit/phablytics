# Python Standard Library Imports
import itertools
import json
import random

# Third Party (PyPI) Imports
import numpy

# Phablytics Imports
from phablytics.constants import COLORS
from phablytics.utils import get_users_by_phid


# isort: off


class TaskMetricsStats:
    def __init__(self, metrics):
        self.metrics = metrics

        self.stats = {}
        self._compute_stats()

        self.aggregated_stats = self._get_aggregated_stats()

    @property
    def metrics_json(self):
        metrics_json = [
            metric.as_dict()
            for metric
            in reversed(self.metrics)
        ]
        return metrics_json

    @property
    def all_tasks_created(self):
        tasks = [
            task
            for metric in reversed(self.metrics)
            for task in metric.tasks_created
        ]
        return tasks

    @property
    def all_tasks_closed(self):
        tasks = [
            task
            for metric in reversed(self.metrics)
            for task in metric.tasks_closed
        ]
        return tasks

    def _compute_stats(self):
        attributes = [
            ('points_completed', 'Story Points Completed', ),
            ('points_added', 'Story Points Added', ),
            ('num_closed', 'Tasks Closed', ),
            ('num_created', 'Tasks Created', ),
            ('num_created_per_total', 'Tasks Created per Total Tasks', ),
            ('ratio', 'Task Open vs Closed Ratio', ),
            ('mean_days_to_resolution', 'Average Days to Resolution', ),
            ('days_to_resolution_per_point', 'Days to Resolution per Story Point', ),
            ('points_per_task', 'Story Points per Task', ),
            ('tasks_per_point', 'Tasks per Discrete Story Point', ),
        ]

        stat_fns = [
            'max',
            'min',
            'mean',
            'median',
        ]

        for attr, name in attributes:
            attr_stats = {
                'name': name,
            }

            values = [getattr(metric, attr) for metric in self.metrics]

            for stat_fn in stat_fns:
                value = getattr(numpy, stat_fn)(values)
                attr_stats[stat_fn] =  value

            self.stats[attr] = attr_stats

    def _get_aggregated_stats(self):
        metric_cls = self.metrics[0].__class__
        period_start = self.metrics[-1].period_start
        period_end = self.metrics[0].period_end
        tasks_created = self.all_tasks_created
        tasks_closed = self.all_tasks_closed

        aggregated_stats = AggregatedTaskMetricsStats(
            metric_cls,
            period_start,
            period_end,
            tasks_created,
            tasks_closed
        )

        return aggregated_stats


class AggregatedTaskMetricsStats:
    def __init__(self, metric_cls, period_start, period_end, tasks_created, tasks_closed):
        self.metric_cls = metric_cls
        self.period_start = period_start
        self.period_end = period_end
        self.tasks_created = tasks_created
        self.tasks_closed = tasks_closed

        self._build_metrics()

    def _build_metrics(self):
        self.stats = {}

        self.metric = self._build_metric(
            'Aggregated',
            self.period_start,
            self.period_end,
            self.tasks_created,
            self.tasks_closed
        )

        self._compute_aggregated_stats()

        self._build_segments()

    def _build_metric(self, name, period_start, period_end, tasks_created, tasks_closed):
        metric = self.metric_cls(
            period_name=name,
            period_start=period_start,
            period_end=period_end,
            tasks_created=tasks_created,
            tasks_closed=tasks_closed
        )
        return metric

    def _compute_aggregated_stats(self):
        metric = self.metric

        attributes = [
            ('points_completed', 'Story Points Completed', ),
            ('points_added', 'Story Points Added', ),
            ('num_closed', 'Tasks Closed', ),
            ('num_created', 'Tasks Created', ),
            ('num_created_per_total', 'Tasks Created per Total Tasks', ),
            ('ratio', 'Task Open vs Closed Ratio', ),
            ('mean_days_to_resolution', 'Average Days to Resolution', ),
            ('days_to_resolution_per_point', 'Days to Resolution per Story Point', ),
            ('points_per_task', 'Story Points per Task', ),
            ('tasks_per_point', 'Tasks per Discrete Story Point', ),
        ]

        for attr, name in attributes:
            attr_stats = {
                'name': name,
                'count': getattr(metric, attr),
            }

            value = getattr(metric, attr)

            # for stat_fn in stat_fns:
            #     attr_stats[stat_fn] =  value

            self.stats[attr] = attr_stats

    def _build_segments(self):
        # X-axis (customer, service, engineer(owner), team)
        # Y-axis (whatever metric)
        self.segments = [
            self._build_customer_segment(),
            self._build_user_segment(),
            self._build_service_segment(),
        ]

    def _build_customer_segment(self):
        # By Customer
        segment = {
            'key': 'tasks_by_customer',
            'name': 'Tasks by Customer',
        }

        tasks_by_customers = {
            customer: list(tasks)
            for customer, tasks
            in itertools.groupby(
                self.tasks_closed,
                lambda task: task.customer_name or 'General'
            )
        }

        metrics = [
            self._build_metric(
                customer,
                self.period_start,
                self.period_end,
                [],
                list(tasks)
            )
            for customer, tasks
            in tasks_by_customers.items()
        ]

        colors = [
            random.choice(COLORS)
            for x
            in range(len(metrics))
        ]

        chart_config_json = {
            'type': 'doughnut',
            'data': {
                'datasets': [
                    {
                        'label': 'Points completed',
                        'name': 'Points completed',
                        'data': [
                            metric.points_completed for metric in metrics
                        ],
                        'backgroundColor': colors,
                    },
                    {
                        'label': 'Tickets Closed',
                        'data': [
                            metric.num_closed for metric in metrics
                        ],
                        'backgroundColor': colors,
                    },
                ],
                'labels': [metric.period_name for metric in metrics],
            },
            'options': {
            },
        }

        segment['metrics'] = metrics
        segment['chart_config_json'] = json.dumps(chart_config_json)

        return segment

    def _build_user_segment(self):
        # By Author/Owner
        segment = {
            'key': 'tasks_by_owner_author',
            'name': 'Tasks by Owner/Author',
        }

        tasks_closed_by_owners = {
            user_phid: list(tasks)
            for user_phid, tasks
            in itertools.groupby(
                self.tasks_closed,
                lambda task: task.owner_phid
            )
            if user_phid
        }

        users_lookup = get_users_by_phid(list(tasks_closed_by_owners.keys()))

        metrics = [
            self._build_metric(
                users_lookup.get(user_phid).username,
                self.period_start,
                self.period_end,
                [],
                tasks,
            )
            for user_phid, tasks
            in tasks_closed_by_owners.items()
        ]

        colors = [
            random.choice(COLORS)
            for x
            in range(len(metrics))
        ]

        # https://www.chartjs.org/samples/latest/charts/doughnut.html
        chart_config_json = {
            'type': 'doughnut',
            'data': {
                'datasets': [
                    {
                        'label': 'Points completed',
                        'data': [
                            metric.points_completed for metric in metrics
                        ],
                        'backgroundColor': colors,
                    },
                    {
                        'label': 'Tickets Closed',
                        'data': [
                            metric.num_closed for metric in metrics
                        ],
                        'backgroundColor': colors,
                    },
                ],
                'labels': [metric.period_name for metric in metrics],
            },
            'options': {
            },
        }

        segment['metrics'] = metrics
        segment['chart_config_json'] = json.dumps(chart_config_json)

        return segment

    def _build_service_segment(self):
        # By Project/Service
        segment = {
            'key': 'tasks_by_service',
            'name': 'Tasks by Service',
        }

        tasks_by_services = {
            service: list(tasks)
            for service, tasks
            in itertools.groupby(
                self.tasks_closed,
                lambda task: task.service_name or 'General'
            )
        }

        metrics = [
            self._build_metric(
                service,
                self.period_start,
                self.period_end,
                [],
                list(tasks)
            )
            for service, tasks
            in tasks_by_services.items()
        ]

        colors = [
            random.choice(COLORS)
            for x
            in range(len(metrics))
        ]

        chart_config_json = {
            'type': 'doughnut',
            'data': {
                'datasets': [
                    {
                        'label': 'Points completed',
                        'name': 'Points completed',
                        'data': [
                            # TODO: fix this
                            # random.randint(1, 100) for metric in metrics
                            metric.points_completed for metric in metrics
                        ],
                        'backgroundColor': colors,
                    },
                    {
                        'label': 'Tickets Closed',
                        'data': [
                            metric.num_closed for metric in metrics
                        ],
                        'backgroundColor': colors,
                    },
                ],
                'labels': [metric.period_name for metric in metrics],
            },
            'options': {
            },
        }

        segment['metrics'] = metrics
        segment['chart_config_json'] = json.dumps(chart_config_json)

        return segment
