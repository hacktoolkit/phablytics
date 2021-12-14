# Python Standard Library Imports
import copy
import os
import uuid

# Third Party (PyPI) Imports
from flask import (
    Flask,
    send_from_directory,
)
from werkzeug.routing import BaseConverter

# Phablytics Imports
from phablytics.settings import CUSTOM_STATIC_DIR
from phablytics.web.explore import explore_page
from phablytics.web.help import help_page
from phablytics.web.home import home_page
from phablytics.web.metrics import metrics_page
from phablytics.web.reports import reports_page
from phablytics.web.utils import custom_render_template as _r


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

STATIC_DIR = os.path.realpath(
    os.path.join(
        os.path.dirname(__file__),
        'static'
    )
)

TEMPLATES_DIR = os.path.realpath(
    os.path.join(
        os.path.dirname(__file__),
        'templates'
    )
)


application = Flask(
    'phablytics',
    static_folder=STATIC_DIR,
    template_folder=TEMPLATES_DIR
)

application.secret_key = os.environ.get('FLASK_SECRET_KEY', uuid.uuid4().hex)
application.url_map.converters['regex'] = RegexConverter


application.register_blueprint(explore_page)
application.register_blueprint(help_page)
application.register_blueprint(home_page)
application.register_blueprint(metrics_page)
application.register_blueprint(reports_page)


@application.errorhandler(404)
def page_not_found(e):
    return _r('404.html')


@application.route('/custom_static/<path:filename>')
def custom_static(filename):
    return send_from_directory(CUSTOM_STATIC_DIR, filename)
