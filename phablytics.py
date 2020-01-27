# Python Standard Library Imports
import argparse

from htk import slack_message
from phablytics.reports import RevisionStatusReport


class PhablyticsCLI:
    REPORT_TYPES = {
        'RevisionStatus' : RevisionStatusReport,
    }

    def __init__(self):
        pass

    def execute(self):
        self.parse_args()
        if self.report_type:
            report_class = self.REPORT_TYPES.get(self.report_type)
            if report_class:
                report = report_class().generate_report()
                if self.slack:
                    slack_channel = self.slack_channel
                    slack_message(text=report, channel=slack_channel)
                else:
                    print(report)

    def parse_args(self):
        arg_parser = argparse.ArgumentParser(description='Phablytics report generator.')
        arg_parser.add_argument(
            '-r', '--report_type',
            help=f"Report type (options: {', '.join(self.REPORT_TYPES.keys())}).",
            required=True
        )
        arg_parser.add_argument(
            '--slack',
            help='Output report to Slack.',
            action='store_true',
            required=False
        )
        arg_parser.add_argument(
            '--slack_channel',
            help='Slack channel to use for displaying report.',
            required=False
        )

        cli_args = arg_parser.parse_args(namespace=self)
        self.arg_parser = arg_parser


def main():
    PhablyticsCLI().execute()


if __name__ == '__main__':
    main()
