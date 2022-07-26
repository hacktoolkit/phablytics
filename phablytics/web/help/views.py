# Third Party (PyPI) Imports
from flask import Blueprint

# Phablytics Imports
from phablytics.web.utils import custom_render_template as _r


help_endpoints = Blueprint(
    'help_endpoints',
    __name__,
    template_folder='templates'
)


@help_endpoints.route('')
def index():
    return _r('help.html')
