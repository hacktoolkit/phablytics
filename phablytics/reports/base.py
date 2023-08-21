# Python Standard Library Imports
import typing as T
from dataclasses import asdict

# Third Party (PyPI) Imports
import markdown
from htk.utils.slack import SlackMessage

# Phablytics Imports
from phablytics.repos import report_last_run_repo
from phablytics.utils import hours_ago


# isort: off


class PhablyticsReport:
    """This is the base class for other Phablytics reports.
    """
    def __init__(self, report_config, *args, **kwargs):
        self.report_config = report_config

        for key, value in asdict(report_config).items():
            setattr(self, key, value)

    def _prepare_report(self):
        """Any prep logic for generating a report

        Subclasses SHOULD override this method
        """
        pass

    @property
    def web_url(self):
        from phablytics.web.reports.utils import get_report_url
        url = get_report_url(self.name)
        return url

    @property
    def last_run_timestamp(self):
        ts = report_last_run_repo.get_last_run(self.report_config.name)
        return ts

    @property
    def last_run_hours_ago(self) -> T.Optional[int]:
        last_run_timestamp = self.last_run_timestamp
        if last_run_timestamp is None:
            hours = None
        else:
            hours = hours_ago(last_run_timestamp)

        return hours

    def generate_report(self, *args, **kwargs) -> T.Union[T.List[SlackMessage], str]:
        """The main function to generate a report

        Subclasses MAY override this method
        """
        self._prepare_report()

        if self.slack:
            report = self.generate_slack_report()
        elif self.html:
            report = self.generate_html_report()
        else:
            report = self.generate_text_report()

        save_last_run = kwargs.pop('save_last_run', False)
        if save_last_run:
            report_last_run_repo.save_last_run(self.report_config.name)
            # print(f'Last run at: {self.last_run_timestamp} / {self.last_run_hours_ago} hours ago')

        return report

    def generate_slack_report(self) -> T.List[SlackMessage]:
        """Generates a Slack report

        Subclasses MUST override this method
        """
        raise Exception('Not implemented')

    def generate_text_report(self) -> str:
        """Generates a text report

        Subclasses MAY override this method

        It turns out, however, that generating a text report
        from the Slack version is not a bad default
        """
        slack_report = self.generate_slack_report()

        report = []

        for slack_message in slack_report:
            report.append(slack_report.text)
            report.append('')

            count = 0
            for attachment in slack_report.attachments:
                if count > 0:
                    report.append('')

                report.append(attachment.get('pretext', ''))
                report.append(attachment['text'])
                count += 1

        report_string = '\n'.join(report).encode('utf-8').decode('utf-8',)

        return report_string

    def generate_html_report(self) -> str:
        """Generates an HTML report

        Subclasses MAY override this method
        """
        text_report = self.generate_text_report()
        html_report = markdown.markdown(text_report)
        return html_report
