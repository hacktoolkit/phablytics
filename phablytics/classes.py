# Python Standard Library Imports
import datetime
import re
from functools import cached_property

# Third Party (PyPI) Imports
import markdown

# Phablytics Imports
from phablytics.constants import SERVICE_PREFIX

# Local Imports
from .settings import (
    CUSTOMERS,
    GROUPS,
    PHABRICATOR_INSTANCE_BASE_URL,
    REVISION_ACCEPTANCE_THRESHOLD,
)


DATE_FORMAT = '%Y-%m-%d'


# isort: off


class PhabricatorEntity:
    def __init__(self, raw_data):
        self.raw_data = raw_data

    ##
    # Primary attributes

    @property
    def id_(self):
        id_ = self.raw_data['id']
        return id_

    @property
    def phid(self):
        phid = self.raw_data['phid']
        return phid

    @property
    def type_(self):
        type_ = self.raw_data['type']
        return type_

    ##
    # Fields attributes

    @property
    def created_ts(self):
        ts = self.fields['dateCreated']
        return ts

    @property
    def created_at(self):
        created_at = datetime.datetime.fromtimestamp(self.created_ts)
        return created_at

    @property
    def created_at_str(self):
        return self.created_at.strftime(DATE_FORMAT)

    @property
    def modified_ts(self):
        ts = self.fields['dateModified']
        return ts

    @property
    def modified_at(self):
        modified_at = datetime.datetime.fromtimestamp(self.modified_ts)
        return modified_at

    @property
    def modified_at_str(self):
        return self.modified_at(DATE_FORMAT)

    @property
    def closed_ts(self):
        ts = self.fields['dateClosed']
        return ts

    @property
    def closed_at(self):
        closed_at = datetime.datetime.fromtimestamp(self.closed_ts) if self.closed_ts else None
        return closed_at

    @property
    def closed_at_str(self):
        closed_at = self.closed_at
        value = closed_at.strftime(DATE_FORMAT) if closed_at else ''
        return value

    @property
    def name(self):
        name = self.fields['name']
        return name

    @property
    def status(self):
        status = self.fields['status']
        return status

    @property
    def status_value(self):
        status_value = self.status['value']
        return status_value

    ##
    # Top-level attributes

    @property
    def fields(self):
        fields = self.raw_data['fields']
        return fields

    @property
    def attachments(self):
        attachments = self.raw_data['attachments']
        return attachments


class Maniphest(PhabricatorEntity):
    def __str__(self):
        value = f'**[{self.task_id}]({self.url})** {self.name} *({self.status_value}, {self.points} pts)*'
        return value

    @property
    def html(self):
        html = markdown.markdown(self.__str__())
        return html

    ##
    # Primary attributes

    @property
    def task_id(self):
        formatted_task_id = f'T{self.id_}'
        return formatted_task_id

    @property
    def url(self):
        url = f'{PHABRICATOR_INSTANCE_BASE_URL}/{self.task_id}'
        return url

    ##
    # Fields attributes

    @property
    def author_phid(self):
        phid = self.fields['authorPHID']
        return phid

    @property
    def owner_phid(self):
        owner_phid = self.fields['ownerPHID']
        return owner_phid

    @property
    def points(self):
        points = float(self.fields['points'] or 0)
        return points

    ##
    # Nested attributes

    @property
    def project_phids(self):
        project_phids = [
            phid
            for phid
            in self.attachments.get('projects', {}).get('projectPHIDs', [])
        ]
        return project_phids

    @cached_property
    def projects(self):
        from phablytics.utils import lookup_project_by_phid
        projects = [
            lookup_project_by_phid(phid)
            for phid
            in self.project_phids
        ]
        return projects

    ##
    # Derived attributes

    @property
    def days_to_resolution(self):
        closed_at = self.closed_at
        created_at = self.created_at

        if closed_at is not None:
            days = (closed_at - created_at).days
        else:
            days = 0

        return days

    @cached_property
    def services(self):
        from phablytics.utils import lookup_project_by_phid

        services = [
            project
            for project
            in self.projects
            if project and project.name.startswith(SERVICE_PREFIX)
        ]
        return services

    @cached_property
    def service_name(self):
        if len(self.services) == 1:
            service_name = self.services[0].service_name
        elif len(self.services) > 1:
            service_name = 'Multiple'
        else:
            service_name = None
        return service_name

    @cached_property
    def customers(self):
        from phablytics.utils import is_customer

        customers = [
            project
            for project
            in self.projects
            if is_customer(project)
        ]
        return customers

    @cached_property
    def customer_name(self):
        if len(self.customers) == 1:
            customer_name = self.customers[0].customer_name
        elif len(self.customers) > 1:
            customer_name = 'Multiple'
        else:
            customer_name = None
        return customer_name


class Project(PhabricatorEntity):
    @property
    def attachments(self):
        attachments = self.raw_data.get('attachments', {})
        return attachments

    @property
    def member_phids(self):
        members = self.attachments.get('members', {}).get('members', [])
        member_phids = [
            member['phid']
            for member
            in members
        ]
        return member_phids

    @property
    def parent(self):
        parent_raw_data = self.fields.get('parent', None)
        parent = Project(parent_raw_data) if parent_raw_data else None
        return parent

    ##
    # Derived properties

    @property
    def customer_name(self):
        return CUSTOMERS['formatter'](self.name)

    @property
    def service_name(self):
        if self.name.startswith(SERVICE_PREFIX):
            service_name = self.name[len(SERVICE_PREFIX):]
        else:
            service_name = None
        return service_name


class ProjectColumn(PhabricatorEntity):
    pass


class Repo(PhabricatorEntity):
    ##
    # Primary attributes

    @property
    def full_name(self):
        full_name = self.raw_data['fullName']
        return full_name

    ##
    # Computed attributes

    @property
    def symbolic_name(self):
        name = self.full_name.split(' ')[0]
        return name

    @property
    def slug(self):
        name = self.full_name.split(' ')[1]
        return name

    @property
    def repository_url(self):
        url = f'{PHABRICATOR_INSTANCE_BASE_URL}/source/{self.slug}'
        return url


class Revision(PhabricatorEntity):
    ##
    # Primary attributes

    @property
    def revision_id(self):
        formatted_rev_id = f'D{self.id_}'
        return formatted_rev_id

    @property
    def url(self):
        url = f'{PHABRICATOR_INSTANCE_BASE_URL}/{self.revision_id}'
        return url

    @property
    def repo_phid(self):
        phid = self.fields['repositoryPHID']
        return phid

    @property
    def title(self):
        title = self.fields['title'].strip()
        return title

    @property
    def author_phid(self):
        phid = self.fields['authorPHID']
        return phid

    ##
    # Nested attributes

    @property
    def reviewers(self):
        reviewers = self.attachments['reviewers']['reviewers']
        return reviewers

    @property
    def reviewer_phids(self):
        """Gets the reviewer PHIDs for this revision
        """
        reviewers = self.reviewers
        phids = [reviewer['reviewerPHID'] for reviewer in reviewers]
        return phids

    @property
    def is_accepted(self):
        is_accepted = self.status_value == 'accepted'
        return is_accepted

    ##
    # Relational attributes

    def get_acceptor_phids(self, include_groups=False):
        """Get PHIDs of accepting reviewer entities

        If `include_groups` is True, only include USER reviewers,
        else, also includes group (PROJ) reviewers.
        """
        reviewers = self.reviewers
        phids = [
            reviewer['reviewerPHID']
            for reviewer
            in reviewers
            if (
                reviewer.get('status') == 'accepted'
                and (
                    include_groups
                    or 'USER' in reviewer['reviewerPHID']
                )
            )
        ]
        return phids

    @property
    def acceptor_phids(self):
        phids = self.get_acceptor_phids(include_groups=False)
        return phids

    @property
    def group_acceptor_phids(self):
        phids = self.get_acceptor_phids(include_groups=True)
        return phids

    @property
    def num_acceptors(self):
        return len(self.acceptor_phids)

    def get_blocker_phids(self, include_groups=False):
        """Get PHIDs of blocking reviewer entities
        """
        def _is_blocking(reviewer):
            is_blocking = False
            if reviewer.get('isBlocking'):
                is_blocking = True
            elif (
                reviewer['status'] in ['blocking', 'rejected']
                and (
                    include_groups
                    or 'USER' in reviewer['reviewerPHID']
                )
            ):
                is_blocking = True
            else:
                pass

            return is_blocking

        reviewers = self.reviewers
        phids = [
            reviewer['reviewerPHID']
            for reviewer
            in reviewers
            if _is_blocking(reviewer)
        ]
        return phids

    @property
    def blocker_phids(self):
        phids = self.get_blocker_phids(include_groups=False)
        return phids

    @property
    def group_blocker_phids(self):
        phids = self.get_blocker_phids(include_groups=True)
        return phids

    @property
    def num_blockers(self):
        return len(self.blocker_phids)

    def has_sufficient_non_group_reviewer_acceptances(self, user_phids, acceptance_threshold):
        """Determines whether this revision has sufficient acceptances meeting or exceeding `acceptance_threshold`

        Accepting reviewers must be:
        - actual users, not groups
        - not a member of the blocking reviewer group (not in `user_phids`)
        """
        non_group_acceptances = 0

        user_phids_set = set(user_phids)
        for reviewer in self.reviewers:
            reviewer_phid = reviewer['reviewerPHID']
            if (
                reviewer_phid not in user_phids_set
                and 'USER' in reviewer_phid

                and reviewer.get('status') == 'accepted'
            ):
                non_group_acceptances += 1
        else:
            pass

        has_sufficient_acceptances = non_group_acceptances >= acceptance_threshold
        return has_sufficient_acceptances

    def has_reviewer_among_group(self, user_phids):
        has_reviewer = False

        user_phids_set = set(user_phids)

        for reviewer in self.reviewers:
            if reviewer['reviewerPHID'] in user_phids_set:
                has_reviewer = True
                break

        return has_reviewer

    ##
    # Computed attributes

    @property
    def meets_acceptance_criteria(self):
        value = self.is_accepted and len(self.acceptor_phids) >= REVISION_ACCEPTANCE_THRESHOLD
        return value

    @property
    def is_wip(self):
        title = self.title
        is_wip = title.startswith('WIP') or title.startswith('[WIP]') or title.endswith('WIP')
        return is_wip


class User(PhabricatorEntity):
    def as_group(self):
        """Sometimes, Users are actually Groups, so convert to a Group
        when this is detected
        """
        assert self.is_group
        group_data = GROUPS[self.username]
        group = Group(self.raw_data, group_data)
        return group

    ##
    # Primary attributes

    @property
    def name(self):
        name = self.raw_data.get('name')
        if name is None and 'fields' in self.raw_data:
            name = self.raw_data['fields'].get('realName') or self.raw_data['fields'].get('username')

        return name

    @property
    def username(self):
        username = self.fields.get('username', self.name)
        return username

    @property
    def is_group(self):
        """Checks to see if this User is actually a Group
        """
        is_group = self.username in GROUPS
        return is_group

    @property
    def profile_url(self):
        if self.is_group:
            # this is a group, show the group profile page instead
            url = self.as_group().profile_url
        else:
            # this is a regular user
            url = f'{PHABRICATOR_INSTANCE_BASE_URL}/p/{self.username}'
        return url

    @property
    def fields(self):
        """Overwrites PhabricatorEntity.fields

        NOTE: Users might get instantiated with partial data, without ['fields']
        """

        fields = self.raw_data.get('fields', {})
        return fields


class Group(PhabricatorEntity):
    def __init__(self, raw_data, group_data=None, *args, **kwargs):
        super(Group, self).__init__(raw_data, *args, **kwargs)

        self.group_data = group_data

    @property
    def group_id(self):
        group_id = self.group_data['id']
        return group_id

    @property
    def profile_url(self):
        url = f'{PHABRICATOR_INSTANCE_BASE_URL}/project/members/{self.group_id}'
        return url
