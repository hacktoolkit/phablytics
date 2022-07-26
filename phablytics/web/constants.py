SITE_NAME = 'Phablytics'


NAV_LINKS = [
    {
        'name': 'Home',
        'path': '/',
    },
    {
        'name': 'Explore',
        'path': '/explore',
    },
    {
        'name': 'Metrics',
        'path': '/metrics',
    },
    {
        'name': 'Reports',
        'path': '/reports',
    },
    {
        'name': 'Users',
        'path': '/users',
    },
    {
        'name': 'Help',
        'path': '/help',
    },
]


# Breadcrumbs are automatically inflected based on the final phrase of a URL path.
# Overrides can be set based on paths in the BREADCRUMB_OVERRIDES dict.
BREADCRUMB_OVERRIDES = {
    '/' : 'Home',
    '/explore': 'Explore',
    '/metrics': 'Metrics',
    '/metrics/alltasks': 'All Tasks',
    '/reports': 'Reports',
    '/users': 'Users',
    '/help': 'Help',
}
