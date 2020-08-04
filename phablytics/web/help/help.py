
# Third Party (PyPI) Imports
from flask import Blueprint

# Phablytics Imports
from phablytics.web.utils import custom_render_template as _r


help_page = Blueprint(
    'help_page',
    __name__,
    template_folder='templates'
)


@help_page.route('/help')
def index():
    return _r('help.html')
