# Python Standard Library Imports
from collections import namedtuple

# Phablytics Imports
from phablytics.reports.base import PhablyticsReport
from phablytics.reports.utils import (
    SlackMessage,
    pluralize_noun,
)
from phablytics.settings import (
    UPCOMING_PROJECT_TASKS_DUE_REPORT_COLUMN_NAMES,
    UPCOMING_PROJECT_TASKS_DUE_REPORT_CUSTOM_EXCLUSIONS,
    UPCOMING_PROJECT_TASKS_DUE_REPORT_EXCLUDED_TASKS,
    UPCOMING_PROJECT_TASKS_DUE_REPORT_ORDER,
    UPCOMING_PROJECT_TASKS_DUE_REPORT_PROJECT_NAME,
    UPCOMING_PROJECT_TASKS_DUE_THRESHOLD_LOWER_HOURS,
    UPCOMING_PROJECT_TASKS_DUE_THRESHOLD_UPPER_HOURS,
)
from phablytics.utils import (
    get_maniphest_tasks_by_project_name,
    get_project_columns_by_project_name,
)


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
