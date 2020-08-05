# Python Standard Library Imports
import argparse
import pprint

# Third Party (PyPI) Imports
from htk import slack_message

# Local Imports
from .reports.utils import (
    get_report_config,
    get_report_names,
    get_report_types,
)
from .utils import (
    adhoc,
    whoami,
)


class PhablyticsCLI:
    def __init__(self):
        self.report_names = get_report_names()
        self.report_types = get_report_types()

    def execute(self):
        self.parse_args()

        if self.test:
            pass
        elif self.adhoc:
            response = adhoc(self.adhoc, method_args=self.adhoc_args)
            pprint.pprint(response)
        elif self.whoami:
            user = whoami()
            pprint.pprint(user.raw_data)
        elif self.report_name:
            report_config = get_report_config(self.report_name, self)
            report_class = self.report_types.get(report_config.report_type)
            if report_class:
                report = report_class(report_config).generate_report()
                if report_config.slack:
                    slack_channel = report_config.slack_channel
                    slack_message(
                        text=report.text,
                        attachments=report.attachments,
                        channel=slack_channel,
                        username=report.username,
                        icon_emoji=report.emoji
                    )
                else:
                    print(report)
            else:
                raise Exception(f'Invalid report type: {report_config.report_type}')

    def parse_args(self):
        arg_parser = argparse.ArgumentParser(description='Phablytics report generator.')
        report_name_choices = sorted(self.report_names)
        arg_parser.add_argument(
            '-r', '--report_name',
            help=f"Report name.",
            choices=report_name_choices,
            required=False
        )
        arg_parser.add_argument(
            '--slack',
            action='store_true',
            help='Output report to Slack.',
            required=False
        )
        arg_parser.add_argument(
            '--slack-channel',
            help='Slack channel to use for displaying report.',
            required=False
        )
        arg_parser.add_argument(
            '-t', '--test',
            action='store_true',
            help='Test. Development use only.',
            required=False
        )
        arg_parser.add_argument(
            '-a', '--adhoc',
            help='Runs an adhoc Conduit method.',
            required=False
        )
        arg_parser.add_argument(
            '--adhoc-args',
            help='Specifies arguments for Conduit method, used with --adhoc.',
            required=False
        )
        arg_parser.add_argument(
            '-w', '--whoami',
            action='store_true',
            help='Runs whoami.',
            required=False
        )

        cli_args = arg_parser.parse_args(namespace=self)
        self.arg_parser = arg_parser


def main():
    PhablyticsCLI().execute()


if __name__ == '__main__':
    main()
