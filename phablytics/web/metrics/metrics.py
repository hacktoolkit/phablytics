# Python Standard Library Imports
import json

# Third Party (PyPI) Imports
from flask import Blueprint

# Phablytics Imports
from phablytics.metrics.metrics import (
    METRICS,
    Metrics,
)
from phablytics.web.utils import custom_render_template as _r


metrics_page = Blueprint(
    'metrics_page',
    __name__,
    template_folder='templates'
)


@metrics_page.route('/metrics', defaults={'page': 'index'})
def index(page):
    context_data = {
        'metrics': METRICS,
    }

    return _r('metrics/%s.html' % page, context_data=context_data)


@metrics_page.route('/metrics/<page>')
def show_metric(page):
    metrics = getattr(Metrics(), page)()
    metrics_json = [
        metric.as_dict()
        for metric
        in reversed(metrics)
    ]

    context_data = {
        'metrics': metrics,
        'metrics_json': json.dumps(metrics_json),
    }

    return _r('metrics/%s.html' % page, context_data=context_data)
