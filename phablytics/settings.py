# Python Standard Library Imports
import os


##
# Various Settings and Configuration Variables

PHABRICATOR_INSTANCE_BASE_URL = 'configure_me'

# Reports
REVISION_AGE_THRESHOLD_DAYS = 14
REVISION_ACCEPTANCE_THRESHOLD = 2
REVISION_STATUS_REPORT_QUERY_KEY = 'configure_me'

UPCOMING_PROJECT_TASKS_DUE_REPORT_PROJECT_NAME = 'configure_me'
UPCOMING_PROJECT_TASKS_DUE_REPORT_COLUMN_NAMES = []
UPCOMING_PROJECT_TASKS_DUE_REPORT_ORDER = [
    '-id', # oldest tasks first
]
UPCOMING_PROJECT_TASKS_DUE_REPORT_EXCLUDED_TASKS = []
UPCOMING_PROJECT_TASKS_DUE_REPORT_CUSTOM_EXCLUSIONS = []

RECENT_TASKS_REPORT_USERNAMES = []


##
# Import Local Settings if `./local_settings.py` exists

LOCAL_SETTINGS_FILENAME = os.path.realpath(os.path.join(os.path.dirname(__file__), 'local_settings.py'))

if os.path.isfile(LOCAL_SETTINGS_FILENAME):
    from .local_settings import *
