# Python Standard Library Imports
import json

# Third Party (PyPI) Imports
from flask import Blueprint

# Phablytics Imports
from phablytics.metrics.metrics import (
    METRICS,
    Metrics,
)
from phablytics.web.metrics.forms import (
    MetricsFilterForm,
    get_filter_params,
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
    filter_params = get_filter_params()
    filter_form = MetricsFilterForm(**filter_params)

    stats = getattr(Metrics(), page)(**filter_params)

    context_data = {
        'metrics': stats.metrics,
        'stats': stats.stats,
        'metrics_json': json.dumps(stats.metrics_json),
        'aggregated_stats': stats.aggregated_stats,
        'filter_params': filter_params,
        'filter_form': filter_form,
    }

    return _r('metrics/%s.html' % page, context_data=context_data)
