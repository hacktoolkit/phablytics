# Python Standard Library Imports
import copy

# Third Party (PyPI) Imports
from flask import (
    Blueprint,
    url_for,
)

# Phablytics Imports
from phablytics.utils import (
    fetch_users,
    get_user_by_username,
)
from phablytics.web.utils import custom_render_template as _r


users_endpoints = Blueprint(
    'users_endpoints',
    __name__,
    template_folder='templates'
)


@users_endpoints.route('', defaults={'page': 'index'})
def index(page):
    context_data = {
        'users': fetch_users(),
    }
    return _r('users/%s.html' % page, context_data=context_data)


@users_endpoints.route('/<username>')
def user_profile(username):
    user = get_user_by_username(username)
    context_data = {
        'user': user,
    }
    return _r('users/profile.html', context_data=context_data)
