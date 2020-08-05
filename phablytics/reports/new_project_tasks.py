# Python Standard Library Imports
import datetime
from collections import namedtuple

# Phablytics Imports
from phablytics.reports.base import PhablyticsReport
from phablytics.reports.utils import (
    SlackMessage,
    pluralize_noun,
)
from phablytics.utils import get_maniphest_tasks_by_project_name


class NewProjectTasksReport(PhablyticsReport):
    """The New Project Tasks Report shows a list of tickets
    Created in the last N hours that are in the Open and Unassigned state
    """
    HEADING = 'New Tasks'

    def __init__(self, *args, **kwargs):
        super(NewProjectTasksReport, self).__init__(*args, **kwargs)

    @property
    def timeline(self):
        timeline = f'Created in the last {self.threshold_lower_hours} hours'
        return timeline

    class _ReportSection(namedtuple('ReportSection', 'column_phid,column,tasks')):
        pass

    def _prepare_report(self):

        def _should_include(task):
            # filter out assigned tasks
            should_include = (
                task.owner_phid is None
                and task.created_at > datetime.datetime.now() - datetime.timedelta(hours=self.threshold_lower_hours)
            )
            return should_include

        report_sections = []
        all_maniphest_tasks = []

        for project_name in self.project_names:
            maniphest_tasks = get_maniphest_tasks_by_project_name(
                project_name,
                column_phids=None,
                order=self.order,
            )
            all_maniphest_tasks.extend(maniphest_tasks)

        tasks = filter(_should_include, all_maniphest_tasks)

        report_sections.append(self._ReportSection(
            # column_phid=None,
            # column=None,
            None,
            None,
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
                    # 'pretext': f"*{count} {report_section.column.name} {pluralize_noun('Task', count)}*:",
                    'text': '\n'.join(report).encode('utf-8').decode('utf-8'),
                    'color': colors[len(attachments) % len(colors)],
                })
            else:
               # omit section if no tasks for that section
                pass

        project_names_str = ', '.join(self.project_names)
        slack_text = f'*{project_names_str} - {self.HEADING}* _({self.timeline})_'

        if len(attachments) == 0:
            slack_text = '{}\n{}'.format(
                slack_text,
                '_All caught up -- there are no tasks for this section._'
            )

        report = SlackMessage(
            text=slack_text,
            attachments=attachments,
            username=self.slack_username,
            emoji=self.slack_emoji
        )

        return report
