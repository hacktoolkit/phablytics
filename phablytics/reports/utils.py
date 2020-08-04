# Python Standard Library Imports
from collections import namedtuple


def get_report_types():
    """Returns a mapping of report types to classes
    """
    # Phablytics Imports
    from phablytics.reports import (
        NewProjectTasksReport,
        RecentTasksReport,
        RevisionStatusReport,
        UpcomingProjectTasksDueReport,
        UrgentAndOverdueProjectTasksReport,
    )

    report_types = {
        'NewProjectTasks': NewProjectTasksReport,
        'RevisionStatus' : RevisionStatusReport,
        'UpcomingProjectTasksDue' : UpcomingProjectTasksDueReport,
        'UrgentAndOverdueProjectTasks' : UrgentAndOverdueProjectTasksReport,
        'RecentTasks' : RecentTasksReport,
    }
    return report_types


class SlackMessage(namedtuple('SlackMessage', 'text,attachments')):
    pass


def pluralize_noun(noun, count):
    """Adds 's' to `noun` depending on `count`
    """
    suffix = '' if count == 1 else 's'  # 'pluralize 0 or many
    pluralized = noun + suffix
    return pluralized


def pluralize_verb(verb, n_subjects):
    """Adds 's' to `verb` for singular `n_subjects`
    """
    if verb in ('is', 'are',):
        pluralized = pluralize_tobe_verb(n_subjects)
    else:
        suffix = 's' if n_subjects == 1 else ''
        pluralized = verb + suffix

    return pluralized


def pluralize_tobe_verb(n_subjects):
    pluralized = 'is' if n_subjects == 1 else 'are'
    return pluralized
