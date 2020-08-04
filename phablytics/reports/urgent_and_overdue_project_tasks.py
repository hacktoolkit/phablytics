# Phablytics Imports
from phablytics.reports.upcoming_tasks_due import UpcomingProjectTasksDueReport
from phablytics.settings import (
    URGENT_AND_OVERDUE_TASKS_REPORT_CUSTOM_EXCLUSIONS,
    URGENT_AND_OVERDUE_TASKS_THRESHOLD_HOURS,
)


class UrgentAndOverdueProjectTasksReport(UpcomingProjectTasksDueReport):
    """A special case of `UpcomingProjectTasksDueReport`

    Tasks that are either due within 24 hours, or in the past (overdue)
    """
    HEADING = 'Urgent or Overdue Tasks'
    EXCLUSIONS = URGENT_AND_OVERDUE_TASKS_REPORT_CUSTOM_EXCLUSIONS
    TIMELINE = f'past due - within {URGENT_AND_OVERDUE_TASKS_THRESHOLD_HOURS} hours'
