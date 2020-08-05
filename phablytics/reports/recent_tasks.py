# Phablytics Imports
from phablytics.reports.base import PhablyticsReport
from phablytics.reports.utils import SlackMessage
from phablytics.utils import (
    get_maniphest_tasks_by_owners,
    get_users_by_username,
)


class RecentTasksReport(PhablyticsReport):
    def __init__(self, *args, **kwargs):
        super(RecentTasksReport, self).__init__(*args, **kwargs)

    def generate_text_report(self):
        usernames = self.report_config.usernames
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
        report = SlackMessage(
            text=text,
            attachments=None,
            username=self.slack_username,
            emoji=self.slack_emoji
        )
        return report
