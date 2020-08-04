# Third Party (PyPI) Imports
from flask import Blueprint

# Phablytics Imports
from phablytics.web.utils import custom_render_template as _r


home_page = Blueprint(
    'home_page',
    __name__,
    template_folder='templates'
)


@home_page.route('/')
def index():
    return _r('index.html')
