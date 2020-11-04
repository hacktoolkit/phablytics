# Python Standard Library Imports
import os
import sys
from dataclasses import (
    dataclass,
    field,
)


##
# Various Settings and Configuration Variables

PHABLYTICS_BASE_URL = None
PHABRICATOR_INSTANCE_BASE_URL = 'configure_me'

ADMIN_USERNAME = 'configure_me'

GROUPS = {
    'example-group-the-incredibles' : {
        'id': 9000,
    },
}

REVISION_ACCEPTANCE_THRESHOLD = 2

# Reports


@dataclass
class ReportConfig:
    name: str
    report_type: str
    html: bool = False
    # Slack
    slack: bool = False
    slack_channel: str = None
    slack_username: str = 'Phablytics Bot'
    slack_emoji: str = None
    # Shared fields
    query_key: str = None
    order: list = field(
        default_factory=lambda: [
            '-id',  # oldest tasks first
        ]
    )
    # ReviewStatus
    reviewers: list = field(default_factory=list)
    group_reviewers: list = field(default_factory=list)
    non_group_reviewer_acceptance_threshold: int = 2
    # RevisionStatus
    threshold_days: int = 14
    # NewProjectTasks
    project_names: list = field(default_factory=list)
    # UpcomingProjectTasksDue, UrgentAndOverdueTasks, NewProjectTasks
    project_name: str = None
    column_names: list = field(default_factory=list)
    threshold_lower_hours: int = 24  # 1 day
    threshold_upper_hours: int = 96  # 4 days
    excluded_tasks: list = field(default_factory=list)
    custom_exclusions: list = field(default_factory=list)
    # RecentTasks, RevisionStatus
    usernames: list = field(default_factory=list)


TEAM_USERNAMES = []


REPORTS = [
    # These are sample ReportConfigs that should be customized in your local settings.py
    ReportConfig(
        name='GroupReviewStatus',
        report_type='GroupReviewStatus',
        reviewers=[
        ],
        group_reviewers=[
            'configure_me',
        ],
        threshold_days=30
    ),
    ReportConfig(
        name='RevisionStatus',
        report_type='RevisionStatus',
        query_key='configure_me',
        threshold_days=14
    ),
    ReportConfig(
        name='NewProjectTasks',
        report_type='NewProjectTasks',
        project_names=[
            'configure_me'
        ]
    ),
    ReportConfig(
        name='UpcomingProjectTasksDue',
        report_type='UpcomingProjectTasksDue',
        project_name=None,
        column_names=[],
        excluded_tasks=[],
        custom_exclusions=[]
    ),
    ReportConfig(
        name='UrgentAndOverdueProjectTasks',
        report_type='UrgentAndOverdueProjectTasks',
        project_name=None,
        column_names=[],
        excluded_tasks=[],
        custom_exclusions=[]
    ),
    ReportConfig(
        name='RecentTasks',
        report_type='RecentTasks',
        usernames=TEAM_USERNAMES,
        slack=False,
        slack_channel=None
    ),
]


##
# Import Local Settings if `local_settings.py` exists in CWD

LOCAL_SETTINGS_FILENAME = os.path.realpath(os.path.join(os.getcwd(), 'settings.py'))

if os.path.isfile(LOCAL_SETTINGS_FILENAME):
    sys.path.append(os.path.dirname(LOCAL_SETTINGS_FILENAME))
    # Third Party (PyPI) Imports
    from settings import *
