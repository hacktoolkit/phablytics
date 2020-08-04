# Python Standard Library Imports
import datetime
from collections import namedtuple

# Phablytics Imports
from phablytics.reports.base import PhablyticsReport
from phablytics.reports.utils import (
    SlackMessage,
    pluralize_noun,
)
from phablytics.settings import (
    NEW_PROJECT_TASKS_BOARD_NAMES,
    NEW_PROJECT_TASKS_THRESHOLD_HOURS,
)
from phablytics.utils import get_maniphest_tasks_by_project_name


class NewProjectTasksReport(PhablyticsReport):
    """The New Project Tasks Report shows a list of tickets
    Created in the last N hours that are in the Open and Unassigned state
    """
    HEADING = 'New Project Tasks'
    TIMELINE = f'Created in the last {NEW_PROJECT_TASKS_THRESHOLD_HOURS} hours'

    def __init__(self, order=None, *args, **kwargs):
        if order is None:
            order = [
                # '-dateModified',
                '-updated',
                '-fulltext-modified',
                '-fulltext-created',
                '-id',
            ]

        self.project_name = NEW_PROJECT_TASKS_BOARD_NAMES

        self.order = order

        super(NewProjectTasksReport, self).__init__(*args, **kwargs)

    class _ReportSection(namedtuple('ReportSection', 'column_phid,column,tasks')):
        pass

    def _prepare_report(self):

        def _should_include(task):
            # filter out assigned tasks
            should_include = (
                task.owner_phid is None
                and task.created_at > datetime.datetime.now() - datetime.timedelta(hours=NEW_PROJECT_TASKS_THRESHOLD_HOURS)
            )
            return should_include

        report_sections = []
        maniphest_tasks = get_maniphest_tasks_by_project_name(
            self.project_name,
            column_phids=None,
            order=self.order,
        )

        tasks = filter(_should_include, maniphest_tasks)

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

        slack_text = f'*{self.project_name} - {self.HEADING}* _({self.TIMELINE})_'

        if len(attachments) == 0:
            slack_text = '{}\n{}'.format(
                slack_text,
                '_All caught up -- there are no tasks for this section._'
            )

        report = SlackMessage(slack_text, attachments)

        return report
