# Python Standard Library Imports
import datetime
import random

# Third Party (PyPI) Imports
import emoji
from htk.utils.slack import SlackMessage

# Phablytics Imports
from phablytics.reports.constants import (
    DIFF_ABSENT_MESSAGES,
    DIFF_PRESENT_MESSAGES,
    HTML_ICON_SEPARATOR,
)
from phablytics.reports.revision_status import RevisionStatusReport
from phablytics.reports.utils import (
    pluralize_noun,
    pluralize_verb,
)
from phablytics.settings import REVISION_ACCEPTANCE_THRESHOLD
from phablytics.utils import (
    fetch_differential_revisions,
    get_projects_by_name,
    get_repos_by_phid,
    get_users_by_phid,
    get_users_by_username,
)


# isort: off


class GroupReviewStatusReport(RevisionStatusReport):
    """The Group Review Status Report shows a list of Diffs with
    particular reviewers added.

    A typical use case would be a shared library that is
    maintained by a group of core developers.
    """
    def __init__(self, *args, **kwargs):
        super(GroupReviewStatusReport, self).__init__(*args, **kwargs)

    def _prepare_report(self):
        """Prepares the Revision Status Report
        """
        # get revisions
        reviewer_users = get_users_by_username(self.reviewers)
        projects = get_projects_by_name(self.group_reviewers, include_members=True)
        group_reviewer_phids = [
            member_phid
            for project in projects
            for member_phid in project.member_phids
        ]
        reviewer_phids = list(map(lambda x: x.phid, reviewer_users + projects))

        non_group_reviewer_acceptance_threshold = self.non_group_reviewer_acceptance_threshold

        date_created = (datetime.datetime.now() - datetime.timedelta(days=self.threshold_days)).replace(hour=0, minute=0, second=0)
        active_revisions = fetch_differential_revisions(
            reviewer_phids=reviewer_phids,
            modified_after_dt=date_created
        )
        revisions_ready_for_group_review = list(
            filter(
                lambda revision: revision.has_sufficient_non_group_reviewer_acceptances(
                    group_reviewer_phids,
                    non_group_reviewer_acceptance_threshold
                ),
                active_revisions
            )
        )

        # place revisions into buckets
        revisions_missing_reviewers = []
        revisions_to_review = []
        revisions_with_blocks = []
        revisions_additional_approval = []
        revisions_accepted = []

        for revision in revisions_ready_for_group_review:
            if not revision.has_reviewer_among_group(group_reviewer_phids):
                revisions_missing_reviewers.append(revision)
            elif revision.meets_acceptance_criteria:
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
                    lambda phid: self._get_phid_username(phid) in self.usernames,
                    revision.blocker_phids
                )
            )
            if len(team_blockers) > 0:
                revisions_change_required.append(revision)
            else:
                revisions_blocked.append(revision)

        # finally, assign bucketed revisions
        self.revisions_missing_reviewers = revisions_missing_reviewers
        self.revisions_to_review = revisions_to_review
        self.revisions_change_required = revisions_change_required
        self.revisions_blocked = revisions_blocked
        self.revisions_additional_approval = revisions_additional_approval
        self.revisions_accepted = revisions_accepted

    def generate_slack_report(self):
        """Generates the Revision Status Report with Slack attachments
        """
        attachments = []

        num_revisions = len(self.revisions_missing_reviewers)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_missing_reviewers, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count)

            attachments.append({
                'pretext': f":hourglass: *{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('need', num_revisions)} reviewers assigned*: _(newest first)_",
                'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
                'color': '#f2c744',
            })

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
                'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
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
                'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
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
                'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
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
                'pretext': f":mag: *{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('need', num_revisions)} additional approvals*: _(newest first)_",
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
                'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
                'color': 'good',
            })

        report = self._build_slack_report_from_attachments(attachments)
        return report

    def generate_text_report(self):
        lines = []

        # Revisions missing reviewers
        num_revisions = len(self.revisions_missing_reviewers)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_missing_reviewers, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count, slack=False)

            icon = emoji.emojize(':hourglass_done:')
            lines.append(f"{icon}{HTML_ICON_SEPARATOR}**{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('need', num_revisions)} reviewers assigned**: *(newest first)*")
            lines.append('')
            lines.append('\n'.join(report).encode('utf-8').decode('utf-8'))

        # Revisions with 0 reviews
        num_revisions = len(self.revisions_to_review)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_to_review, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count, slack=False)

            icon = emoji.emojize(':warning:')
            lines.append(f"{icon}{HTML_ICON_SEPARATOR}**{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('need', num_revisions)} to be reviewed**: *(newest first)*")
            lines.append('')
            lines.append('\n'.join(report).encode('utf-8').decode('utf-8'))

        # Revisions with team blockers - change required
        num_revisions = len(self.revisions_change_required)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_change_required, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count, slack=False)

            icon = emoji.emojize(':arrows_counterclockwise:', use_aliases=True)
            lines.append(f"{icon}{HTML_ICON_SEPARATOR}**{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('require', num_revisions)} changes**: *(newest first)*")
            lines.append('')
            lines.append('\n'.join(report).encode('utf-8').decode('utf-8'))

        # Revisions with only external blockers
        num_revisions = len(self.revisions_blocked)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_blocked, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count, slack=False)

            icon = emoji.emojize(':no_entry_sign:', use_aliases=True)
            lines.append(f"{icon}{HTML_ICON_SEPARATOR}**{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('is', num_revisions)} blocked**: *(newest first)*")
            lines.append('')
            lines.append('\n'.join(report).encode('utf-8').decode('utf-8'))

        # Revisions with 1 approval
        num_revisions = len(self.revisions_additional_approval)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_additional_approval, key=lambda r: r.modified_ts, reverse=True):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count, slack=False)

            icon = emoji.emojize(':mag:', use_aliases=True)
            lines.append(f"{icon}{HTML_ICON_SEPARATOR}**{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('need', num_revisions)} additional approvals**: *(newest first)*")
            lines.append('')
            lines.append('\n'.join(report).encode('utf-8').decode('utf-8'))

        # Revisions Accepted
        num_revisions = len(self.revisions_accepted)
        if num_revisions > 0:
            report = []
            count = 0

            for revision in sorted(self.revisions_accepted, key=lambda r: r.modified_ts):
                count += 1
                self._format_and_append_revision_to_report(report, revision, count, slack=False)

            icon = emoji.emojize(':white_check_mark:', use_aliases=True)
            lines.append(f"{icon}{HTML_ICON_SEPARATOR}**{num_revisions} {pluralize_noun('Diff', num_revisions)} {pluralize_verb('is', num_revisions)} accepted and ready to land**: *(oldest first)*")
            lines.append('')
            lines.append('\n'.join(report).encode('utf-8').decode('utf-8'))

        text_report = '\n'.join(lines)
        return text_report
