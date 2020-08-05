# Phablytics Imports
from phablytics.reports.upcoming_tasks_due import UpcomingProjectTasksDueReport


class UrgentAndOverdueProjectTasksReport(UpcomingProjectTasksDueReport):
    """A special case of `UpcomingProjectTasksDueReport`

    Tasks that are either due within 24 hours, or in the past (overdue)
    """
    HEADING = 'Urgent or Overdue Tasks'

    @property
    def timeline(self):
        timeline = f'past due - within {self.threshold_upper_hours} hours'
        return timeline
