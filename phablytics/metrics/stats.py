# Third Party (PyPI) Imports
import numpy


class TaskMetricsStats:
    def __init__(self, metrics):
        self.metrics = metrics

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
            'num_created',
            'num_closed',
            'points_added',
            'points_completed',
            'ratio',
        ]

        stat_fns = [
            'max',
            'min',
            'mean',
            'median',
        ]

        for attr in attributes:
            values = [getattr(metric, attr) for metric in self.metrics]

            for stat_fn in stat_fns:
                value = getattr(numpy, stat_fn)(values)
                stat_name = '{}_{}'.format(attr, stat_fn)
                setattr(self, stat_name, value)
