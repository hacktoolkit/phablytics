# Python Standard Library Imports
import datetime

# Local Imports
from .settings import GROUPS
from .settings import PHABRICATOR_INSTANCE_BASE_URL
from .settings import REVISION_ACCEPTANCE_THRESHOLD


DATE_FORMAT = '%Y-%m-%d'


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
    def owner_phid(self):
        owner_phid = self.fields['ownerPHID']
        return owner_phid


class Project(PhabricatorEntity):
    pass


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

    @property
    def acceptor_phids(self):
        """Get PHIDs of accepting reviewer entities that are users
        """
        reviewers = self.reviewers
        phids = [
            reviewer['reviewerPHID']
            for reviewer
            in reviewers
            if reviewer.get('status') == 'accepted' and 'USER' in reviewer['reviewerPHID']
        ]
        return phids

    @property
    def num_acceptors(self):
        return len(self.acceptor_phids)

    @property
    def blocker_phids(self):
        """Get PHIDs of blocking reviewer entities
        """
        def _is_blocking(reviewer):
            is_blocking = False
            if reviewer.get('isBlocking'):
                is_blocking = True
            elif reviewer['status'] == 'rejected' and 'USER' in reviewer['reviewerPHID']:
                is_blocking = True

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
    def num_blockers(self):
        return len(self.blocker_phids)

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
