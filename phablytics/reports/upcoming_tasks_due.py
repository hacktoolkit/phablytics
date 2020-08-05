# Python Standard Library Imports
from collections import namedtuple

# Phablytics Imports
from phablytics.reports.base import PhablyticsReport
from phablytics.reports.utils import (
    SlackMessage,
    pluralize_noun,
)
from phablytics.utils import (
    get_maniphest_tasks_by_project_name,
    get_project_columns_by_project_name,
)


class UpcomingProjectTasksDueReport(PhablyticsReport):
    """The Upcoming Project Tasks Due Report shows a list of tasks ordered by creation date or custom key.
    """
    HEADING = 'Upcoming Tasks Due Soon'

    def __init__(self, *args, **kwargs):
        super(UpcomingProjectTasksDueReport, self).__init__(*args, **kwargs)

    class _ReportSection(namedtuple('ReportSection', 'column_phid,column,tasks')):
        pass

    @property
    def timeline(self):
        timeline = f'within the next {self.threshold_lower_hours} - {self.threshold_upper_hours} hours'
        return timeline

    def _prepare_report(self):
        if self.column_names:
            columns = get_project_columns_by_project_name(self.project_name, self.column_names)
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
                task.id_ not in self.excluded_tasks
                and not any([
                    custom_exclusion(task)
                    for custom_exclusion
                    in self.custom_exclusions
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

        slack_text = f'*{self.project_name} - {self.HEADING}* _({self.timeline})_'

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
