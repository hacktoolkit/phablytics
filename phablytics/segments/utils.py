# Python Standard Library Imports
from collections import namedtuple

# Phablytics Imports
from phablytics.settings import (
    CUSTOM_SEGMENTS,
    PROJECT_TEAM_NAMES,
)
from phablytics.utils import (
    get_all_projects,
    get_customers,
)


class Segment:
    was_seeded = False
    all_projects = None
    previously_segmented = None

    @classmethod
    def seed(cls):
        cls.was_seeded = True

        cls.all_projects = get_all_projects()

        customers = sorted(get_customers(), key=lambda x: x.name)
        teams = sorted([project for project in cls.all_projects if project.name in PROJECT_TEAM_NAMES], key=lambda x: x.name)

        segments = [
            Segment('Customers', projects=customers),
            Segment('Teams', projects=teams),
        ]

        cls.previously_segmented = {
            project.name: True
            for segment
            in segments
            for project in segment.projects
        }

        return segments

    def __init__(self, name, projects=None, **kwargs):
        self.name = name
        self.cfg = kwargs

        if projects:
            self.projects = projects
        else:
            self._build_segment()

    def _build_segment(self):
        cfg = self.cfg

        if cfg.get('segments'):
            self.segments = [Segment(**segment_cfg) for segment_cfg in cfg['segments']]
            self.projects = [
                project
                for segment in self.segments
                for project in segment.projects
            ]
        else:
            self.segments = None
            projects = list(filter(
                lambda project: project.name not in Segment.previously_segmented,
                Segment.all_projects
            ))

            if cfg.get('include'):
                projects = list(filter(
                    lambda project: project.name in cfg['include'],
                    projects
                ))

            if cfg.get('filter'):
                projects = list(filter(
                    lambda project: cfg['filter'](project),
                    projects
                ))

            if cfg.get('exclude'):
                projects = list(filter(
                    lambda project: not cfg['exclude'](project),
                    projects
                ))

            self.projects = projects

        for project in self.projects:
            Segment.previously_segmented[project.name] = True

    @property
    def projects_str(self):
        return ','.join([project.name for project in self.projects])


def build_project_segments():
    segments = Segment.seed()

    for custom_segment_cfg in CUSTOM_SEGMENTS:
        segment = Segment(**custom_segment_cfg)
        segments.append(segment)

    return segments
