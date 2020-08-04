class PhablyticsReport:
    """This is the base class for other Phablytics reports.
    """
    def __init__(self, as_slack=False, *args, **kwargs):
        self.as_slack = as_slack

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

        if self.as_slack:
            report = self.generate_slack_report()
        else:
            report = self.generate_text_report()

        return report

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
            report.append(attachment['pretext'])
            report.append(attachment['text'])
            count += 1

        report_string = '\n'.join(report).encode('utf-8').decode('utf-8',)

        return report_string
