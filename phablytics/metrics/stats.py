# Third Party (PyPI) Imports
import numpy


class TaskMetricsStats:
    def __init__(self, metrics):
        self.metrics = metrics
        self.stats = {}

        self._compute_stats()

    @property
    def metrics_json(self):
        metrics_json = [
            metric.as_dict()
            for metric
            in reversed(self.metrics)
        ]
        return metrics_json

    def _compute_stats(self):
        attributes = [
            ('points_completed', 'Story Points Completed', ),
            ('points_added', 'Story Points Added', ),
            ('num_closed', 'Tasks Closed', ),
            ('num_created', 'Tasks Created', ),
            ('ratio', 'Task Open vs Closed Ratio', ),
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
