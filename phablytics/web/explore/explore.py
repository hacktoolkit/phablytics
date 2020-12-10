# Third Party (PyPI) Imports
from flask import Blueprint

# Phablytics Imports
from phablytics.segments.utils import build_project_segments
from phablytics.web.utils import custom_render_template as _r


explore_page = Blueprint(
    'explore_page',
    __name__,
    template_folder='templates'
)


@explore_page.route('/explore')
def index():
    segments = build_project_segments()
    context_data = {
        'segments': segments,
    }

    return _r('explore/explore.html', context_data=context_data)
