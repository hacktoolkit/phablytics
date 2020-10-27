# Python Standard Library Imports
from collections import namedtuple
from dataclasses import (
    asdict,
    dataclass,
    field,
)

# Phablytics Imports
from phablytics.settings import (
    REPORTS,
    ReportConfig,
)


def get_report_names():
    report_names = [report.name for report in REPORTS]
    return report_names


def get_report_config(report_name, overrides=None):
    cfg = list(filter(lambda cfg: cfg.name == report_name, REPORTS))[0]
    report_config_dict = asdict(cfg)

    if overrides:
        for key in report_config_dict.keys():
            if hasattr(overrides, key):
                value = getattr(overrides, key)
                if value:
                    report_config_dict[key] = value

    report_config = ReportConfig(**report_config_dict)

    return report_config


def get_report_types():
    """Returns a mapping of report types to classes
    """
    # Phablytics Imports
    from phablytics.reports import (
        GroupReviewStatusReport,
        NewProjectTasksReport,
        RecentTasksReport,
        RevisionStatusReport,
        UpcomingProjectTasksDueReport,
        UrgentAndOverdueProjectTasksReport,
    )

    report_types = {
        'GroupReviewStatus' : GroupReviewStatusReport,
        'NewProjectTasks': NewProjectTasksReport,
        'RecentTasks' : RecentTasksReport,
        'RevisionStatus' : RevisionStatusReport,
        'UpcomingProjectTasksDue' : UpcomingProjectTasksDueReport,
        'UrgentAndOverdueProjectTasks' : UrgentAndOverdueProjectTasksReport,
    }
    return report_types


@dataclass
class SlackMessage:
    text: str = None
    attachments: list = field(default_factory=list)
    username: str = None
    emoji: str = None


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
