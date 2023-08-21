# Python Standard Library Imports
import datetime
import functools
from collections import namedtuple

# Third Party (PyPI) Imports
from htk.utils.slack import SlackMessage

# Phablytics Imports
from phablytics.reports.base import PhablyticsReport
from phablytics.reports.utils import pluralize_noun
from phablytics.utils import (
    get_maniphest_tasks_by_project_name,
    get_maniphest_tasks_by_project_names,
)


class NewProjectTasksReport(PhablyticsReport):
    """The New Project Tasks Report shows a list of tickets
    created in the last N hours that are in the Open and Unassigned state

    N is determined either by a fixed number, or dynamically, using
    the last run timestamp. See `self.lower_hours()`
    """
    HEADING = 'New Tasks'

    def __init__(self, *args, **kwargs):
        super(NewProjectTasksReport, self).__init__(*args, **kwargs)

    @functools.cached_property
    def lower_hours(self):
        """Tasks created newer than this many hours ago should be included

        Default: `self.threshold_lower_hours` or `self.last_run_hours_ago`
        """
        lower_hours = None
        if self.use_last_run_timestamp:
            lower_hours = self.last_run_hours_ago or self.threshold_upper_hours
        else:
            lower_hours = self.threshold_lower_hours
        return lower_hours

    @property
    def timeline(self):
        timeline = f'Created in the last {self.lower_hours} hours'
        return timeline

    class _ReportSection(namedtuple('ReportSection', 'column_phid,column,tasks')):
        pass

    def _prepare_report(self):

        def _should_include(task):
            should_include = (
                # exclude assigned tasks
                task.owner_phid is None
                # exclude tasks created prior to `self.lower_hours`
                and task.created_at > (datetime.datetime.now() - datetime.timedelta(hours=self.lower_hours))
            )
            return should_include

        report_sections = []
        all_maniphest_tasks = []

        if self.projects_and_vs_or == 'and':
            all_maniphest_tasks = get_maniphest_tasks_by_project_names(
                self.project_names,
                column_phids=None,
                order=self.order,
            )
        elif self.projects_and_vs_or == 'or':
            for project_name in self.project_names:
                maniphest_tasks = get_maniphest_tasks_by_project_name(
                    project_name,
                    column_phids=None,
                    order=self.order,
                )
                all_maniphest_tasks.extend(maniphest_tasks)
        else:
            raise Exception(f'Invalid value for `projects_and_vs_or`: {self.projects_and_vs_or}')

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

        join_char = ' & ' if self.projects_and_vs_or == 'and' else ' | '
        project_names_str = join_char.join(self.project_names)
        slack_text = f'*{project_names_str} - {self.HEADING}* _({self.timeline})_'

        if len(attachments) == 0:
            slack_text = '{}\n{}'.format(
                slack_text,
                '_All caught up -- there are no tasks for this section._'
            )

        report = [
            SlackMessage(
                text=slack_text,
                attachments=attachments,
                username=self.slack_username,
                icon_emoji=self.slack_emoji
            ),
        ]

        return report

    def generate_text_report(self):
        lines = []
        project_names_str = ', '.join(self.project_names)
        lines.append(f'**{project_names_str} - {self.HEADING}** *({self.timeline})*')
        lines.append('')

        for report_section in self.report_sections:
            report = []
            count = 0

            for task in report_section.tasks:
                count += 1
                task_link = f'[{task.task_id}]({task.url})'
                report.append(f'{count}. {task_link}  - *{task.name}*')

            if count > 0:
                lines.append('\n'.join(report).encode('utf-8').decode('utf-8'))
            else:
               # omit section if no tasks for that section
                pass

        text_report = '\n'.join(lines)
        return text_report
