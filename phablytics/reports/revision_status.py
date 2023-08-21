# Python Standard Library Imports
import datetime
import random
import typing as T
from dataclasses import dataclass

# Third Party (PyPI) Imports
import emoji
from htk.utils.slack import SlackMessage

# Phablytics Imports
from phablytics.reports.base import PhablyticsReport
from phablytics.reports.constants import (
    DIFF_ABSENT_MESSAGES,
    DIFF_PRESENT_MESSAGES,
    HTML_ICON_SEPARATOR,
)
from phablytics.reports.utils import (
    pluralize_noun,
    pluralize_verb,
)
from phablytics.settings import REVISION_ACCEPTANCE_THRESHOLD
from phablytics.utils import (
    fetch_differential_revisions,
    get_repos_by_phid,
    get_users_by_phid,
)


# isort: off


@dataclass
class ReportSectionConfig:
    revisions: list
    emoji: str
    suffix: str
    order_asc: bool = True
    slack_color: str = None
    include_in_slack: bool = True

    @property
    def num_revisions(self):
        return len(self.revisions)

    @property
    def order_str(self):
        value = ('oldest' if self.order_asc else 'newest') + ' first'
        return value


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
        if phid is not None:
            self.repo_phids.append(phid)
        else:
            # do nothing
            # likely/somehow, a diff or revision does not have an associated repository
            pass

    def _lookup_phids(self):
        """Build lookup tables for User and Repo phids in batch
        """
        self.users_lookup = get_users_by_phid(self.user_phids)
        self.repos_lookup = get_repos_by_phid(self.repo_phids)

    def _prepare_report(self):
        """Prepares the Revision Status Report
        """
        # get revisions
        date_created = (datetime.datetime.now() - datetime.timedelta(days=self.threshold_days)).replace(hour=0, minute=0, second=0)
        active_revisions = fetch_differential_revisions(
            self.query_key,
            modified_after_dt=date_created
        )

        # place revisions into buckets
        revisions_wip = []
        revisions_to_review = []
        revisions_with_blocks = []
        revisions_additional_approval = []
        revisions_accepted = []

        for revision in active_revisions:
            if revision.meets_acceptance_criteria:
                revisions_accepted.append(revision)
            elif revision.is_wip:
                revisions_wip.append(revision)
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
        self.revisions_wip = revisions_wip
        self.revisions_to_review = revisions_to_review
        self.revisions_change_required = revisions_change_required
        self.revisions_blocked = revisions_blocked
        self.revisions_additional_approval = revisions_additional_approval
        self.revisions_accepted = revisions_accepted

    def _get_phid_username(self, phid):
        user = self.users_lookup[phid]
        return user.name

    def _format_user_phid(self, phid, slack=True):
        user = self.users_lookup[phid]
        if slack:
            formatted = f'*<{user.profile_url}|{user.name}>*'
        else:
            formatted = f'**[{user.name}]({user.profile_url})**'
        return formatted

    def _format_and_append_revision_to_report(self, report, revision, count, slack=True):
        repo = self.repos_lookup.get(revision.repo_phid)

        if repo is None:
            repo_link = 'N/A'
        else:
            if slack:
                repo_link = f'<{repo.repository_url}|{repo.slug}>'
            else:
                repo_link = f'[{repo.slug}]({repo.repository_url})'

        acceptors = [f'{self._format_user_phid(phid, slack=slack)}' for phid in revision.acceptor_phids]
        blockers = [f'{self._format_user_phid(phid, slack=slack)}' for phid in revision.blocker_phids]

        MAX_LENGTH = 50
        revision_title = revision.title if len(revision.title) < MAX_LENGTH else (revision.title[:MAX_LENGTH - 3] + '...')

        if slack:
            item = f'{count}. <{revision.url}|{revision.revision_id}> - `{repo_link}` - _{revision_title}_ by {self._format_user_phid(revision.author_phid, slack=slack)}'  # noqa
        else:
            item = f'{count}. [{revision.revision_id}]({revision.url}) - <code>{repo_link}</code> - *{revision_title}* by {self._format_user_phid(revision.author_phid, slack=slack)}'  # noqa
        report.append(item)

        reviewers_msg = []

        if len(acceptors) > 0:
            icon = ':heavy_check_mark:'
            icon_separator = ' ' if slack else HTML_ICON_SEPARATOR

            if not slack:
                icon = emoji.emojize(icon, use_aliases=True)

            reviewers_msg.append(f"{icon}{icon_separator}{', '.join(acceptors)}")

        if len(blockers) > 0:
            if len(reviewers_msg) > 0:
                reviewers_msg.append('; ')
            else:
                pass

            icon = ':no_entry_sign:'
            icon_separator = ' ' if slack else HTML_ICON_SEPARATOR

            if not slack:
                icon = emoji.emojize(icon, use_aliases=True)

            reviewers_msg.append(f"{icon}{icon_separator}{', '.join(blockers)}")

        if len(reviewers_msg) > 0:
            separator = (' ' * 4) if slack else ('&nbsp;' * 4)
            report.append(f"{separator}{''.join(reviewers_msg)}")

        report.append('')

    def get_report_section_configs(self):
        configs = [
            # Revisions WIP
            ReportSectionConfig(
                revisions=self.revisions_wip,
                emoji=':construction:',
                suffix=f"{pluralize_verb('is', len(self.revisions_wip))} currently WIP",
                order_asc=False,
                slack_color='#ccccc',  # light gray
                include_in_slack=False
            ),
            # Revisions with 0 reviews
            ReportSectionConfig(
                revisions=self.revisions_to_review,
                emoji=':warning:',
                suffix=f"{pluralize_verb('need', len(self.revisions_to_review))} to be reviewed",
                order_asc=False,
                # slack_color='warning'  # Slack-yellow, has an orange hue
                slack_color='#f2c744'  # yellow
            ),
            # Revisions with team blockers - change required
            ReportSectionConfig(
                revisions=self.revisions_change_required,
                emoji=':arrows_counterclockwise:',
                suffix=f"{pluralize_verb('require', len(self.revisions_change_required))} changes",
                order_asc=False,
                slack_color='#e8912d'  # orange
            ),
            # Revisions with only external blockers
            ReportSectionConfig(
                revisions=self.revisions_blocked,
                emoji=':no_entry_sign:',
                suffix=f"{pluralize_verb('is', len(self.revisions_blocked))} blocked",
                order_asc=False,
                slack_color='danger'  # Slack red
            ),
            # Revisions with 1 approval
            ReportSectionConfig(
                revisions=self.revisions_additional_approval,
                emoji=':mag:',
                suffix=f"{pluralize_verb('need', len(self.revisions_additional_approval))} additional approvals",
                order_asc=False,
                slack_color='#439f30'  # blue
            ),
            # Revisions Accepted
            ReportSectionConfig(
                revisions=self.revisions_accepted,
                emoji=':white_check_mark:',
                suffix=f"{pluralize_verb('is', len(self.revisions_accepted))} accepted and ready to land",
                order_asc=True,
                slack_color='good',
            )
        ]

        return configs

    def generate_slack_report(self) -> T.List[SlackMessage]:
        """Generates the Revision Status Report with Slack attachments
        """
        attachments = []

        report_section_configs = self.get_report_section_configs()

        def _build_report_section(report_section_config):
            num_revisions = report_section_config.num_revisions
            if num_revisions > 0:
                report = []
                count = 0

                for revision in sorted(report_section_config.revisions, key=lambda r: r.modified_ts, reverse=not report_section_config.order_asc):
                    count += 1
                    self._format_and_append_revision_to_report(report, revision, count)

                attachments.append({
                    'pretext': f"{report_section_config.emoji} *{num_revisions} {pluralize_noun('Diff', num_revisions)} {report_section_config.suffix}*: _({report_section_config.order_str})_",
                    'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
                    'color': report_section_config.slack_color,
                })

        for report_section_config in report_section_configs:
            if report_section_config.include_in_slack:
                _build_report_section(report_section_config)
            else:
                # exclude sections that might be too noisy for Slack, but include in web
                pass

        report = self._build_slack_report_from_attachments(attachments)
        return report

    def _build_slack_report_from_attachments(self, attachments):
        def _summarize_attachment(attachment):
            pretext = attachment['pretext']
            icon, text = pretext.split(' ', 1)
            summary = '• {} {}'.format(
                icon,
                text.rsplit(':', 1)[0].removeprefix('*').removesuffix('*'),
            )
            return summary


        context = {
            'here': '<!here> ' if len(attachments) > 0 else '',
            'greeting': 'Greetings!',
            'message': random.choice(DIFF_PRESENT_MESSAGES) if len(attachments) > 0 else random.choice(DIFF_ABSENT_MESSAGES),
            'summary': '\n'.join(map(_summarize_attachment, attachments)),
            'web_link': f' or <{self.web_url}|view in web>' if self.web_url else '',
        }

        slack_text = 'Greetings Team!\n\n%(message)s\n\n%(summary)s\n\nSee details in thread%(web_link)s.' % context

        report = [
            # display summary in first message
            SlackMessage(
                text=slack_text,
                username=self.slack_username,
                icon_emoji=self.slack_emoji
            ),
        ] + [
            # display details in thread
            SlackMessage(
                attachments=[attachment],
                username=self.slack_username,
                icon_emoji=self.slack_emoji
            )
            for attachment in attachments
        ]
        return report

    def generate_text_report(self) -> str:
        lines = []

        report_section_configs = self.get_report_section_configs()

        def _build_report_section(report_section_config):
            num_revisions = report_section_config.num_revisions
            if num_revisions > 0:
                report = []
                count = 0

                for revision in sorted(report_section_config.revisions, key=lambda r: r.modified_ts, reverse=not report_section_config.order_asc):
                    count += 1
                    self._format_and_append_revision_to_report(report, revision, count, slack=False)

                icon = emoji.emojize(report_section_config.emoji, use_aliases=True)

                lines.append(f"{icon}{HTML_ICON_SEPARATOR}**{num_revisions} {pluralize_noun('Diff', num_revisions)} {report_section_config.suffix}**: *({report_section_config.order_str})*")
                lines.append('')
                lines.append('\n'.join(report).encode('utf-8').decode('utf-8'))

        for report_section_config in report_section_configs:
            _build_report_section(report_section_config)

        text_report = '\n'.join(lines)
        return text_report
