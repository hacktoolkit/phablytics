# Python Standard Library Imports
import datetime
import random
from collections import namedtuple

# Local Imports
from .settings import RECENT_TASKS_REPORT_USERNAMES
from .settings import REVISION_ACCEPTANCE_THRESHOLD
from .settings import REVISION_AGE_THRESHOLD_DAYS
from .settings import REVISION_STATUS_REPORT_QUERY_KEY
from .settings import TEAM_USERNAMES
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_COLUMN_NAMES
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_CUSTOM_EXCLUSIONS
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_EXCLUDED_TASKS
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_ORDER
from .settings import UPCOMING_PROJECT_TASKS_DUE_REPORT_PROJECT_NAME
from .settings import UPCOMING_PROJECT_TASKS_DUE_THRESHOLD_LOWER_HOURS
from .settings import UPCOMING_PROJECT_TASKS_DUE_THRESHOLD_UPPER_HOURS
from .settings import URGENT_AND_OVERDUE_TASKS_REPORT_CUSTOM_EXCLUSIONS
from .settings import URGENT_AND_OVERDUE_TASKS_THRESHOLD_HOURS
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
        'UrgentAndOverdueProjectTasks' : UrgentAndOverdueProjectTasksReport,
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

    def _prepare_report(self):
        """Any prep logic for generating a report

        Subclasses SHOULD override this method
        """
        pass

    def generate_report(self, *args, **kwargs):
        """The main function to generate a report

        Subclasses MAY override this method
        """
        self._prepare_report()

        if self.as_slack:
            report =self.generate_slack_report()
        else:
            report =self.generate_text_report()

        return report

    def generate_text_report(self):
        """Generates a text report

        Subclasses MAY override this method

        It turns out, however, that generating a text report
        from the Slack version is not a bad default
        """
        slack_report = self.generate_slack_report()

        report = []
        report.append(slack_report.text)
        report.append('')

        count = 0
        for attachment in slack_report.attachments:
            if count > 0:
                report.append('')
            report.append(attachment['pretext'])
            report.append(attachment['text'])
            count += 1

        report_string = '\n'.join(report).encode('utf-8').decode('utf-8',)

        return report_string


def pluralize_noun(noun, count):
    """Adds 's' to `noun` depending on `count`
    """
    suffix = '' if count == 1 else 's'  # 'pluralize 0 or many
    pluralized = noun + suffix
    return pluralized


def pluralize_verb(verb, n_subjects):
    """Adds 's' to `verb` for singular `n_subjects`
    """
    if verb in ('is', 'are',):
        pluralized = pluralize_tobe_verb(n_subjects)
    else:
        suffix = 's' if n_subjects == 1 else ''
        pluralized = verb + suffix

    return pluralized


def pluralize_tobe_verb(n_subjects):
    pluralized = 'is' if n_subjects == 1 else 'are'
    return pluralized


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
        # get revisions
        date_created = (datetime.datetime.now() - datetime.timedelta(days=REVISION_AGE_THRESHOLD_DAYS)).replace(hour=0, minute=0, second=0)
        active_revisions = fetch_differential_revisions(
            REVISION_STATUS_REPORT_QUERY_KEY,
            modified_after_dt=date_created
        )

        # place revisions into buckets
        revisions_to_review = []
        revisions_with_blocks = []
        revisions_additional_approval = []
        revisions_accepted = []

        for revision in active_revisions:
            if revision.meets_acceptance_criteria:
                revisions_accepted.append(revision)
            elif revision.is_wip:
                # skip WIP
                pass
            elif revision.num_blockers > 0:
                revisions_with_blocks.append(revision)
            elif 0 < revision.num_acceptors < REVISION_ACCEPTANCE_THRESHOLD:
                revisions_additional_approval.append(revision)
            else:
                # no approvers
                revisions_to_review.append(revision)

            self._add_users(revision.reviewer_phids)
            self._add_users([revision.author_phid])

            self._add_repo(revision.repo_phid)

        # generate lookup tables after iterating through revisions
        self._lookup_phids()

        # split blockers into team blockers and external blockers
        revisions_change_required = []
        revisions_blocked = []

        for revision in revisions_with_blocks:
            team_blockers = list(
                filter(
                    lambda phid: self._get_phid_username(phid) in TEAM_USERNAMES,
                    revision.blocker_phids
                )
            )
            if len(team_blockers) > 0:
                revisions_change_required.append(revision)
            else:
                revisions_blocked.append(revision)

        # finally, assign bucketed revisions
        self.revisions_to_review = revisions_to_review
        self.revisions_change_required = revisions_change_required
        self.revisions_blocked = revisions_blocked
        self.revisions_additional_approval = revisions_additional_approval
        self.revisions_accepted = revisions_accepted

    def _get_phid_username(self, phid):
        user = self.users_lookup[phid]
        return user.name

    def _format_user_phid(self, phid):
        user = self.users_lookup[phid]
        formatted = f'*<{user.profile_url}|{user.name}>*'
        return formatted

    def _format_and_append_revision_to_report(self, report, revision, count):
        repo = self.repos_lookup[revision.repo_phid]
        repo_link = f'<{repo.repository_url}|{repo.slug}>'

        acceptors = [f'{self._format_user_phid(phid)}' for phid in revision.acceptor_phids]
        blockers = [f'{self._format_user_phid(phid)}' for phid in revision.blocker_phids]

        MAX_LENGTH = 50
        revision_title = revision.title if len(revision.title) < MAX_LENGTH else (revision.title[:MAX_LENGTH - 3] + '...')

        report.append(
            f'{count}. <{revision.url}|{revision.revision_id}> - `{repo_link}` - _{revision_title}_ by {self._format_user_phid(revision.author_phid)}'
        )
        reviewers_msg = []
        if len(acceptors) > 0:
            reviewers_msg.append(f":heavy_check_mark: {', '.join(acceptors)}")
        if len(blockers) > 0:
            if len(reviewers_msg) > 0:
                reviewers_msg.append('; ')
            else:
                pass
            reviewers_msg.append(f":no_entry_sign: {', '.join(blockers)}")

        if len(reviewers_msg) > 0:
            report.append(f"    {''.join(reviewers_msg)}")

        report.append('')

    def generate_slack_report(self):
        """Generates the Revision Status Report with Slack attachments
        """
        attachments = []

        # Revisions with 0 reviews
        num_revisions = len(self.revisions_to_review)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_to_review, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f":warning: *{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('need', num_revisions)} to be reviewed*: _(newest first)_",
                'text': '\n'.join(report).encode('utf-8').decode('utf-8',),
                # 'color': 'warning',  # Slack-yellow, has an orange hue
                'color': '#f2c744',
            })

        # Revisions with team blockers - change required
        num_revisions = len(self.revisions_change_required)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_change_required, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f":arrows_counterclockwise: *{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('require', num_revisions)} changes*: _(newest first)_",
                'text': '\n'.join(report).encode('utf-8').decode('utf-8',),
                'color': '#e8912d',  # orange
            })

        # Revisions with only external blockers
        num_revisions = len(self.revisions_blocked)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_blocked, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f":no_entry_sign: *{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('is', num_revisions)} blocked*: _(newest first)_",
                'text': '\n'.join(report).encode('utf-8').decode('utf-8',),
                'color': 'danger',
            })

        # Revisions with 1 approval
        num_revisions = len(self.revisions_additional_approval)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_additional_approval, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f":pray: *{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('need', num_revisions)} additional approvals*: _(newest first)_",
                'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
                'color': '#439fe0',  # blue
            })

        # Revisions Accepted
        num_revisions = len(self.revisions_accepted)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_accepted, key=lambda r: r.modified_ts):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f":white_check_mark: *{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('is', num_revisions)} accepted and ready to land*: _(oldest first)_",
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
    HEADING = 'Upcoming Tasks Due Soon'
    EXCLUSIONS = UPCOMING_PROJECT_TASKS_DUE_REPORT_CUSTOM_EXCLUSIONS
    TIMELINE = f'within the next {UPCOMING_PROJECT_TASKS_DUE_THRESHOLD_LOWER_HOURS} - {UPCOMING_PROJECT_TASKS_DUE_THRESHOLD_UPPER_HOURS} hours'

    def __init__(self, columns=None, order=None, *args, **kwargs):
        if order is None:
            order = UPCOMING_PROJECT_TASKS_DUE_REPORT_ORDER

        self.project_name = UPCOMING_PROJECT_TASKS_DUE_REPORT_PROJECT_NAME
        self.columns = UPCOMING_PROJECT_TASKS_DUE_REPORT_COLUMN_NAMES

        #self.project = project
        #self.columns = columns
        self.order = order

        super(UpcomingProjectTasksDueReport, self).__init__(*args, **kwargs)

    class _ReportSection(namedtuple('ReportSection', 'column_phid,column,tasks')):
        pass

    def _prepare_report(self):
        if self.columns:
            columns = get_project_columns_by_project_name(self.project_name, self.columns)
            column_lookup = {
                column.phid: column
                for column
                in columns
            }
        else:
            column_lookup = {}

        self.column_lookup = column_lookup

        def _should_include(task):
            #import json
            #print(json.dumps(task.raw_data))
            should_include = (
                task.id_ not in UPCOMING_PROJECT_TASKS_DUE_REPORT_EXCLUDED_TASKS
                and not any([
                    custom_exclusion(task)
                    for custom_exclusion
                    in self.EXCLUSIONS
                ])
            )
            return should_include

        report_sections = []
        for column_phid, column in self.column_lookup.items():
            maniphest_tasks = get_maniphest_tasks_by_project_name(
                self.project_name,
                column_phids=[column_phid],
                order=self.order,
            )

            tasks = filter(_should_include, maniphest_tasks)

            report_sections.append(self._ReportSection(
                column_phid,
                column,
                tasks
            ))

        self.report_sections = report_sections

    def generate_slack_report(self):
        colors = [
            '#333333',
            '#666666',
        ]

        attachments = []

        for report_section in self.report_sections:
            report = []
            count = 0

            for task in report_section.tasks:
                count += 1
                task_link = f'<{task.url}|{task.task_id}>'
                report.append(f'{count}. {task_link}  - _{task.name}_')

            if count > 0:
                attachments.append({
                    'pretext': f"*{count} {report_section.column.name} {pluralize_noun('Task', count)}*:",
                    'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
                    'color': colors[len(attachments) % len(colors)],
                })
            else:
                # omit section if no tasks for that section
                pass

        slack_text = f'*{self.project_name} - {self.HEADING}* _({self.TIMELINE})_'

        if len(attachments) == 0:
            slack_text = '{}\n{}'.format(
                slack_text,
                '_All caught up -- there are no tasks for this section._'
            )

        report = SlackMessage(slack_text, attachments)

        return report


class UrgentAndOverdueProjectTasksReport(UpcomingProjectTasksDueReport):
    """A special case of `UpcomingProjectTasksDueReport`

    Tasks that are either due within 24 hours, or in the past (overdue)
    """
    HEADING = 'Urgent or Overdue Tasks'
    EXCLUSIONS = URGENT_AND_OVERDUE_TASKS_REPORT_CUSTOM_EXCLUSIONS
    TIMELINE = f'past due - within {URGENT_AND_OVERDUE_TASKS_THRESHOLD_HOURS} hours'


class RecentTasksReport(PhablyticsReport):
    def __init__(self, *args, **kwargs):
        super(RecentTasksReport, self).__init__(*args, **kwargs)

    def generate_text_report(self):
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

        report_string = '\n'.join(report)

        return report_string

    def generate_slack_report(self):
        text_report = self.generate_text_report()
        text = '```\n%s\n```' % text_report
        report = SlackMessage(text, None)
        return report
