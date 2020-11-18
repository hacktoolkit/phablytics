# Python Standard Library Imports
import copy

# Third Party (PyPI) Imports
from flask import (
    Blueprint,
    url_for,
)

# Phablytics Imports
from phablytics.reports.utils import (
    get_report_config,
    get_report_names,
    get_report_types,
)
from phablytics.settings import REPORTS
from phablytics.web.utils import custom_render_template as _r


reports_page = Blueprint(
    'reports_page',
    __name__,
    template_folder='templates'
)


@reports_page.route('/reports', defaults={'page': 'index'})
def index(page):
    # report_names = get_report_names()
    context_data = {
        'reports': copy.deepcopy(REPORTS),
    }
    return _r('reports/%s.html' % page, context_data=context_data)


@reports_page.route('/reports/<report_name>')
def show(report_name):
    report_config = get_report_config(report_name)
    report_config.slack = False
    report_config.html = True
    report_types = get_report_types()
    report_class = report_types.get(report_config.report_type)
    report = report_class(report_config)
    report_content = report.generate_report()

    context_data = {
        'report_name': report_name,
        'report_content': report_content,
    }
    return _r('reports/view.html', context_data=context_data)
