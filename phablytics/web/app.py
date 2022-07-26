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
from phablytics.web.explore import explore_endpoints
from phablytics.web.help import help_endpoints
from phablytics.web.home import home_endpoints
from phablytics.web.metrics import metrics_endpoints
from phablytics.web.reports import reports_endpoints
from phablytics.web.users import users_endpoints
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


application.register_blueprint(explore_endpoints, url_prefix='/explore')
application.register_blueprint(help_endpoints, url_prefix='/help')
application.register_blueprint(home_endpoints, url_prefix='/')
application.register_blueprint(metrics_endpoints, url_prefix='/metrics')
application.register_blueprint(reports_endpoints, url_prefix='/reports')
application.register_blueprint(users_endpoints, url_prefix='/users')


@application.errorhandler(404)
def page_not_found(e):
    return _r('404.html')


@application.route('/custom_static/<path:filename>')
def custom_static(filename):
    return send_from_directory(CUSTOM_STATIC_DIR, filename)
