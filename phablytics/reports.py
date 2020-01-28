# Python Standard Library Imports
import datetime
import random
from collections import namedtuple

# Local Imports
from .settings import RECENT_TASKS_REPORT_USERNAMES
from .settings import REVISION_ACCEPTANCE_THRESHOLD
from .settings import REVISION_AGE_THRESHOLD_DAYS
from .settings import REVISION_STATUS_REPORT_QUERY_KEY
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_COLUMN_NAMES
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_CUSTOM_EXCLUSIONS
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_EXCLUDED_TASKS
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_ORDER
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_PROJECT_NAME
from .utils import fetch_differential_revisions
from .utils import get_maniphest_tasks_by_owners
from .utils import get_maniphest_tasks_by_project_name
from .utils import get_project_columns_by_project_name
from .utils import get_repos_by_phid
from .utils import get_users_by_phid
from .utils import get_users_by_username


def get_report_types():
    """Returns a mapping of report types to classes
    """
    report_types = {
        'RevisionStatus' : RevisionStatusReport,
        'UpcomingProjectTasksDue' : UpcomingProjectTasksDueReport,
        'RecentTasks' : RecentTasksReport,
    }
    return report_types


class SlackMessage(namedtuple('SlackMessage', 'text,attachments')):
    pass


class PhablyticsReport:
    """This is the base class for other Phablytics reports.
    """
    def __init__(self, as_slack=False, *args, **kwargs):
        self.as_slack = as_slack

    def generate_report(self, *args, **kwargs):
        self._prepare_report()

        if self.as_slack:
            report =self.generate_slack_report()
        else:
            report =self.generate_text_report()

        return report


class RevisionStatusReport(PhablyticsReport):
    """The Revision Status Report shows a list of Diffs being worked on by a team,
    and outputs them based on their acceptance/needs review status
    """
    def __init__(self, *args, **kwargs):
        self.repo_phids = []
        self.user_phids = []

        self.repos_lookup = None
        self.users_lookup = None

        super(RevisionStatusReport, self).__init__(*args, **kwargs)

    def _add_users(self, phids):
        self.user_phids.extend(phids)

    def _add_repo(self, phid):
        self.repo_phids.append(phid)

    def _lookup_phids(self):
        """Build lookup tables for User and Repo phids in batch
        """
        self.users_lookup = get_users_by_phid(self.user_phids)
        self.repos_lookup = get_repos_by_phid(self.repo_phids)

    def _prepare_report(self):
        """Prepares the Revision Status Report
        """
        date_created = (datetime.datetime.now() - datetime.timedelta(days=REVISION_AGE_THRESHOLD_DAYS)).replace(hour=0, minute=0, second=0)
        active_revisions = fetch_differential_revisions(
            REVISION_STATUS_REPORT_QUERY_KEY,
            modified_after_dt=date_created
        )

        # place revisions into buckets
        revisions_accepted = []
        revisions_blocked = []
        revisions_additional_approval = []
        revisions_to_review = []

        for revision in active_revisions:
            if revision.meets_acceptance_criteria:
                revisions_accepted.append(revision)
            elif revision.is_wip:
                # skip WIP
                pass
            elif revision.num_blockers > 0:
                revisions_blocked.append(revision)
            elif 0 < revision.num_acceptors < REVISION_ACCEPTANCE_THRESHOLD:
                revisions_additional_approval.append(revision)
            else:
                # no approvers
                revisions_to_review.append(revision)

            self._add_users(revision.reviewer_phids)
            self._add_users([revision.author_phid])

            self._add_repo(revision.repo_phid)

        self.revisions_accepted = revisions_accepted
        self.revisions_blocked = revisions_blocked
        self.revisions_additional_approval = revisions_additional_approval
        self.revisions_to_review = revisions_to_review

        # generate lookup tables
        self._lookup_phids()

    def _format_and_append_revision_to_report(self, report, revision, count):
        repo = self.repos_lookup[revision.repo_phid]

        author = self.users_lookup[revision.author_phid]
        acceptors = [f'`{self.users_lookup[phid].name}`' for phid in revision.acceptor_phids]
        blockers = [f'`{self.users_lookup[phid].name}`' for phid in revision.blocker_phids]

        report.append(
            f'{count}. _{revision.title}_ (<{revision.url}|{revision.revision_id}>) by `{author.name}` on `{repo.readable_name}`'
        )
        reviewers_msg = []
        if len(acceptors) > 0:
            reviewers_msg.append(f":white_check_mark: accepted by {', '.join(acceptors)}")
        if len(blockers) > 0:
            if len(reviewers_msg) > 0:
                reviewers_msg.append('; ')
            else:
                pass
            reviewers_msg.append(f":no_entry_sign: blocked by {', '.join(blockers)}")

        if len(reviewers_msg) > 0:
            report.append(f"    {''.join(reviewers_msg)}")

        report.append('')

    def generate_text_report(self):
        report = []

        if len(self.revisions_accepted) > 0:
            count = 0
            report.append(f':white_check_mark: *{len(self.revisions_accepted)} Diffs are Accepted and Ready to Land*: _(oldest first)_')
            for revision in sorted(self.revisions_accepted, key=lambda r: r.modified_ts):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)
            report.append('')

        if len(self.revisions_todo) > 0:
            count = 0
            if len(self.revisions_accepted) > 0:
                report.append('')
            else:
                pass

            report.append(f':warning: *{len(self.revisions_todo)} Diffs Need Review*: _(newest first)_')
            for revision in sorted(self.revisions_todo, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)
            report.append('')

        report_string = '\n'.join(report).encode('utf-8').decode('utf-8')
        return report_string

    def generate_slack_report(self):
        attachments = []

        if len(self.revisions_to_review) > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_to_review, key=lambda r: r.modified_ts):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f':warning: *{len(self.revisions_to_review)} Diffs need to be reviewed*: _(newest first)_',
                'text': '\n'.join(report).encode('utf-8').decode('utf-8',),
                'color': 'warning',
            })

        if len(self.revisions_blocked) > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_blocked, key=lambda r: r.modified_ts):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f':no_entry_sign: *{len(self.revisions_blocked)} Diffs are blocked*: _(newest first)_',
                'text': '\n'.join(report).encode('utf-8').decode('utf-8',),
                'color': 'danger',
            })

        if len(self.revisions_additional_approval) > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_additional_approval, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f':pray: *{len(self.revisions_additional_approval)} Diffs need additional approvals*: _(newest first)_',
                'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
                'color': '#439fe0',
            })

        if len(self.revisions_accepted) > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_accepted, key=lambda r: r.modified_ts):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f':white_check_mark: *{len(self.revisions_accepted)} Diffs are accepted and ready to land*: _(oldest first)_',
                'text': '\n'.join(report).encode('utf-8').decode('utf-8',),
                'color': 'good',
            })

        DIFF_PRESENT_MESSAGES = [
            "Let's review some diffs!",
            "It's code review time!",
        ]

        DIFF_ABSENT_MESSAGES = [
            "It's code review time... but what a shame, there are no diffs to review :disappointed:. Let us write more code!",
            'No code reviews today. Enjoy the extra time! :sunglasses:',
        ]

        context = {
            'here' : '<!here> ' if len(attachments) > 0 else '',
            'greeting' : 'Greetings!',
            'message' : random.choice(DIFF_PRESENT_MESSAGES) if len(attachments) > 0 else random.choice(DIFF_ABSENT_MESSAGES),
        }

        slack_text = 'Greetings Team!\n\n%(message)s' % context

        report = SlackMessage(slack_text, attachments)
        return report


class UpcomingProjectTasksDueReport(PhablyticsReport):
    """The Upcoming Project Tasks Due Report shows a list of tasks ordered by creation date or custom key.
    """
    def __init__(self, columns=None, order=None, *args, **kwargs):
        if order is None:
            order = UPCOMING_PROJECT_TASKS_DUE_REPORT_ORDER

        self.project_name = UPCOMING_PROJECT_TASKS_DUE_REPORT_PROJECT_NAME
        self.columns = UPCOMING_PROJECT_TASKS_DUE_REPORT_COLUMN_NAMES

        #self.project = project
        #self.columns = columns
        self.order = order

        super(UpcomingProjectTasksDueReport, self).__init__(*args, **kwargs)

    def generate_report(self):
        if self.columns:
            columns = get_project_columns_by_project_name(self.project_name, self.columns)
            column_phids = [
                column.phid
                for column
                in columns
            ]
        else:
            column_phids = []

        maniphest_tasks = get_maniphest_tasks_by_project_name(
            self.project_name,
            column_phids=column_phids,
            order=self.order,
        )

        def _should_include(task):
            #import json
            #print(json.dumps(task.raw_data))
            should_include = (
                task.id_ not in UPCOMING_PROJECT_TASKS_DUE_REPORT_EXCLUDED_TASKS
                and not any([
                    custom_exclusion(task)
                    for custom_exclusion
                    in UPCOMING_PROJECT_TASKS_DUE_REPORT_CUSTOM_EXCLUSIONS
                ])
            )
            return should_include

        tasks = filter(_should_include, maniphest_tasks)

        report = []
        count = 0

        report.append(f"*{self.project_name} - {', '.join(self.columns)} - Tasks Due Soon*")

        for task in tasks:
            count += 1
            report.append(f'{count}. _{task.name}_ (<{task.url}|{task.task_id}>)')

        report_string = '\n'.join(report).encode('utf-8').decode('utf-8')
        return report_string


class RecentTasksReport(PhablyticsReport):
    def __init__(self, *args, **kwargs):
        super(RecentTasksReport, self).__init__(*args, **kwargs)

    def generate_report(self):
        usernames = RECENT_TASKS_REPORT_USERNAMES
        users = get_users_by_username(usernames)
        users_lookup = {
            user.phid: user
            for user
            in users
        }
        user_phids = list(users_lookup.keys())

        maniphest_tasks = get_maniphest_tasks_by_owners(user_phids)

        report = []

        def _header_row(fmt, labels):
            s = fmt % tuple(labels)
            return s

        def _dash_row(fmt, ncols):
            dashes = '-' * 30
            tu = tuple([dashes] * ncols)
            s = fmt % tu
            s = s.replace(' | ', '-+-')
            return s

        fmt = '%-6.6s | %-12.12s | %-10.10s | %-10.10s | %-10.10s | %s'
        report.append(_header_row(fmt, 'ID OWNER CREATED CLOSED STATUS NAME'.split()))
        report.append(_dash_row(fmt, 6))

        for task in maniphest_tasks:
            cells = [
                task.task_id,
                users_lookup[task.owner_phid].username,
                task.created_at_str,
                task.closed_at_str,
                task.status_value,
                task.name,
            ]

            report.append(fmt % tuple(cells))

        report_string = '```\n%s\n```' % '\n'.join(report)

        return report_string
