# Local Imports
from .settings import PHABRICATOR_INSTANCE_BASE_URL
from .settings import REVISION_ACCEPTANCE_THRESHOLD


class PhabricatorEntity:
    def __init__(self, raw_data):
        self.raw_data = raw_data

    ##
    # Primary attributes

    @property
    def id_(self):
        id_ = self.raw_data['id']
        return id_

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
    def readable_name(self):
        name = self.full_name.split(' ')[1]
        return name


class User(PhabricatorEntity):
    ##
    # Primary attributes

    @property
    def name(self):
        name = self.raw_data['name']
        return name


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

    @property
    def created_ts(self):
        ts = self.fields['dateCreated']
        return ts

    @property
    def modified_ts(self):
        ts = self.fields['dateModified']
        return ts

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
    def status(self):
        status = self.fields['status']
        return status

    @property
    def status_value(self):
        status_value = self.status['value']
        return status_value

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
