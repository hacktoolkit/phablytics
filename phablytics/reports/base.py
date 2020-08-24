# Python Standard Library Imports
from dataclasses import asdict

# Third Party (PyPI) Imports
import markdown


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

    def generate_report(self, *args, **kwargs):
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

        return report

    def generate_slack_report(self):
        """Generates a Slack report

        Subclasses MUST override this method
        """
        raise Exception('Not implemented')

    def generate_text_report(self):
        """Generates a text report

        Subclasses MAY override this method

        It turns out, however, that generating a text report
        from the Slack version is not a bad default
        """
        slack_report = self.generate_slack_report()

        report = []
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

    def generate_html_report(self):
        """Generates an HTML report

        Subclasses MAY override this method
        """
        text_report = self.generate_text_report()
        html_report = markdown.markdown(text_report)
        return html_report
