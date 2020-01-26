# Future Imports
from __future__ import absolute_import

from phabricator import Phabricator

# Local Imports
from .classes import PhabricatorEntity
from .classes import Repo
from .classes import Revision
from .classes import User


PHAB = Phabricator()


def fetch_revisions(query_key, modified_after_dt=None, modified_before_dt=None):
    """Get revisions for `query_key` between `modified_after_dt` and `modified_before_dt`

    https://secure.phabricator.com/conduit/method/differential.revision.search/
    """
    constraints = {}
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


def get_repos_by_phid(phids):
    """Get repos mapping by PHID
    """
    repos_lookup = get_phids(phids, as_object=Repo)
    return repos_lookup


def get_users_by_phid(phids):
    """Get users mapping by PHID
    """
    users_lookup = get_phids(phids, as_object=User)
    return users_lookup
