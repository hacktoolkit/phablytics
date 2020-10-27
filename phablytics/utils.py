# Future Imports
from __future__ import absolute_import

# Python Standard Library Imports
import datetime
import json
import os

# Third Party (PyPI) Imports
from phabricator import Phabricator

# Local Imports
from .classes import (
    Maniphest,
    PhabricatorEntity,
    Project,
    ProjectColumn,
    Repo,
    Revision,
    User,
)


##
# Phabricator / Conduit Utils


PHAB = Phabricator()


def update_interfaces():
    PHAB.update_interfaces()
    whoami()


##
# PHIDs


def get_phids(phids, as_object=PhabricatorEntity):
    """Retrieve objects for arbitrary PHIDs.

    https://secure.phabricator.com/conduit/method/phid.query/
    """
    phids = list(set(phids))  # dedup PHIDs

    results = PHAB.phid.query(phids=phids)

    phid_objects_lookup = {
        phid: as_object(results[phid])
        for phid
        in phids
    }

    return phid_objects_lookup


##
# Adhoc

def adhoc(method_path, method_args=None):
    """Runs an adhoc Conduit method.
    """
    update_interfaces()

    parts = method_path.split('.')
    f = PHAB
    for part in parts:
        if hasattr(f, part):
            f = getattr(f, part)
        else:
            print(f'Bad method_path specified: {method_path}')
            break

    if method_args:
        kwargs = json.loads(method_args)
    else:
        kwargs = {}

    results = f(**kwargs)
    response = results.response
    return response


##
# Differential


def fetch_differential_revisions(
    query_key=None,
    reviewer_phids=None,
    modified_after_dt=None,
    modified_before_dt=None
):
    """Get revisions for `query_key` between `modified_after_dt` and `modified_before_dt`

    https://secure.phabricator.com/conduit/method/differential.revision.search/
    """
    constraints = {
        'statuses': [
            # 'abandoned',
            'accepted',
            # 'changes-planned',
            # 'draft',
            'needs-review',
            'needs-revision',
            # 'published'
        ],
    }

    if reviewer_phids:
        constraints['reviewerPHIDs'] = reviewer_phids
    if modified_after_dt:
        constraints['modifiedStart'] = int(modified_after_dt.timestamp())
    if modified_before_dt:
        constraints['modifiedEnd'] = int(modified_before_dt.timestamp())

    results = PHAB.differential.revision.search(
        queryKey=query_key,
        constraints=constraints,
        attachments={'reviewers': True}
    )

    revisions = [Revision(revision_data) for revision_data in results.data]

    return revisions


##
# Maniphest


def get_maniphest_tasks(constraints, order=None):
    """Get Maniphest tasksa
    https://secure.phabricator.com/conduit/method/maniphest.search/
    """
    tasks = []
    has_more_results = True
    after = None

    if order is None:
        order = [
            '-id',  # oldest first
        ]

    while has_more_results:
        # handle pagination, since limits are 100 at a time
        results = PHAB.maniphest.search(
            constraints=constraints,
            order=order,
            after=after
        )

        cursor = results.get('cursor', {})
        after = cursor.get('after', None)
        has_more_results = after is not None

        tasks.extend([
            Maniphest(task_data)
            for task_data
            in results.data
        ])

    return tasks


def get_maniphest_tasks_by_owners(owner_phids):
    constraints = {
        'assigned': owner_phids,
    }

    tasks = get_maniphest_tasks(constraints)

    return tasks


def get_maniphest_tasks_by_project_name(project_name, column_phids=None, order=None):
    """Get Maniphest tasks for a project
    """
    project = get_project_by_name(project_name)

    constraints = {
        'projects': [
            project.phid,
        ],
        'statuses': [
            'open',
        ],
    }
    if column_phids:
        constraints['columnPHIDs'] = column_phids
    if order is None:
        order = [
            '-id',  # oldest first
        ]

    tasks = get_maniphest_tasks(constraints, order=order)

    return tasks


def get_bugs_created_over_period(period_start, period_end):
    """Returns a list of bugs created over a period
    """
    constraints = {
        'subtypes': [
            'bug',
        ],
        'createdStart': int(period_start.timestamp()),
        'createdEnd': int(period_end.timestamp()),
    }

    tasks = get_maniphest_tasks(constraints)

    return tasks


def get_bugs_closed_over_period(period_start, period_end):
    """Returns a list of bugs created over a period
    """
    constraints = {
        'subtypes': [
            'bug',
        ],
        'closedStart': int(period_start.timestamp()),
        'closedEnd': int(period_end.timestamp()),
    }

    tasks = get_maniphest_tasks(constraints)

    return tasks


##
# Projects


def get_project_by_name(project_name, include_members=False):
    """Get a project by name

    https://secure.phabricator.com/conduit/method/project.search/
    """
    project_name = project_name.strip()
    constraints = {
        'query': project_name,
    }
    attachments = {}
    if include_members:
        attachments['members'] = True
    results = PHAB.project.search(constraints=constraints, attachments=attachments)

    projects = [
        Project(project_data)
        for project_data
        in results.data
        if project_data.get('fields', {}).get('name', '') == project_name  # look for exact match
    ]

    if len(projects) > 0:
        project = projects[0]
    else:
        raise Exception('No project named `{}` found.'.format(project_name))

    return project


def get_projects_by_name(project_names, include_members=False):
    projects = list(
        map(
            lambda x: get_project_by_name(x, include_members=include_members),
            project_names
        )
    )
    return projects


def get_project_columns_by_project_name(project_name, column_names=None):
    """Get information about workboard columns by project

    https://secure.phabricator.com/conduit/method/project.column.search/
    """
    update_interfaces()

    project = get_project_by_name(project_name)

    constraints = {
        'projects': [
            project.phid,
        ],
    }
    results = PHAB.project.column.search(constraints=constraints)
    project_columns = [
        ProjectColumn(column_data)
        for column_data
        in results.data
    ]
    if column_names:
        project_columns = list(filter(lambda column: column.name in column_names, project_columns))

    return project_columns


##
# Repos


def get_repos_by_phid(phids):
    """Get repos mapping by PHID
    """
    repos_lookup = get_phids(phids, as_object=Repo)
    return repos_lookup


##
# Users


def get_users_by_username(usernames):
    constraints = {
        'usernames': usernames,
    }
    results = PHAB.user.search(
        constraints=constraints
    )
    users = [
        user
        for user_data
        in results.data
        if (user := User(user_data)).username in usernames
    ]
    return users


def get_users_by_phid(phids):
    """Get users mapping by PHID
    """
    users_lookup = get_phids(phids, as_object=User)
    return users_lookup


def whoami():
    """Retrieve information about the logged-in user.

    https://secure.phabricator.com/conduit/method/user.whoami/
    """
    results = PHAB.user.whoami()
    user = User(results.response)
    return user
