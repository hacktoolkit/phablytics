# Python Standard Library Imports
import copy
import re

# Third Party (PyPI) Imports
from flask import (
    abort,
    render_template,
    request,
)
from jinja2 import TemplateNotFound

# Phablytics Imports
import phablytics
from phablytics.constants import GITHUB_URL
from phablytics.settings import (
    ADMIN_USERNAME,
    CUSTOM_STYLESHEETS,
    PHABRICATOR_INSTANCE_BASE_URL,
)
from phablytics.web.constants import (
    BREADCRUMB_OVERRIDES,
    NAV_LINKS,
    SITE_NAME,
)


# isort: off


REPORT_PATH_REGEX = re.compile(r'^/reports/[^/]+$')
USER_PROFILE_PATH_REGEX = re.compile(r'^/users/[^/]+$')


def custom_render_template(template_name, context_data=None):
    if context_data is None:
        context_data = {}

    context_data.update(get_context_data())

    try:
        response = render_template(template_name, **context_data)
        return response
    except TemplateNotFound:
        abort(404)


def get_context_data():
    nav_links = get_nav_links()
    active_pages = list(filter(lambda x: x['active'], nav_links))
    active_page = active_pages[0] if len(active_pages) > 0 else None
    breadcrumbs = get_breadcrumbs()

    if active_page:
        page_title = f'{active_page["name"]} | {SITE_NAME}'
    else:
        page_title = SITE_NAME

    context_data = {
        # customizations
        'custom_stylesheets': CUSTOM_STYLESHEETS,
        # page meta
        'nav_links': nav_links,
        'breadcrumbs': breadcrumbs,
        'page_title': page_title,
        # general stuff
        'admin_username': ADMIN_USERNAME,
        'github_url': GITHUB_URL,
        'phablytics_version': phablytics.__version__,
        'phabricator_instance_base_url': PHABRICATOR_INSTANCE_BASE_URL,
    }

    return context_data


def get_nav_links():
    def _format_nav_link(nav_link):
        nav_link = copy.deepcopy(nav_link)
        nav_link['active'] = nav_link['path'] == request.path
        return nav_link

    nav_links = [
        _format_nav_link(nav_link)
        for nav_link
        in NAV_LINKS
    ]
    return nav_links


def is_report_name_path(path):
    result = REPORT_PATH_REGEX.match(path) is not None
    return result


def is_user_profile_path(path):
    result = USER_PROFILE_PATH_REGEX.match(path) is not None
    return result


def get_breadcrumbs():
    breadcrumbs = []

    path_parts = request.path.split('/')
    path_parts = (
        path_parts[:-1]
        if len(path_parts) > 1 and path_parts[-1] == ''
        else path_parts
    )

    for i, path_part in enumerate(path_parts):
        path = '/'.join(path_parts[:i + 1]) or '/'
        path_suffix = '/'.join(path_parts[i + 1:])
        is_active = i + 1 == len(path_parts)

        default_breadcrumb_name = (
            path_part
            if (
                # leave alone if any conditions are satisfied
                is_report_name_path(path)
                or is_user_profile_path(path)
            )
            # else format breadcrumb as Titlecase
            else path_part.title()
        )

        name = BREADCRUMB_OVERRIDES.get(
            path,  # get breadcrumb by full path
            BREADCRUMB_OVERRIDES.get(
                path_suffix,  # get breadcrumb by path_suffix
                default_breadcrumb_name  # fallback: generated breadcrumb based on path
            )
        )
        breadcrumb = {
            'name': name,
            'url': path,
            'is_active': is_active,
        }
        breadcrumbs.append(breadcrumb)

    return breadcrumbs


def format_choices(options, include_blank=False):
    choices = [('', '', )] if include_blank else []
    choices.extend([(option, option, ) for option in options])
    return choices
