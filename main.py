from htk import slack_message
from phablytics.reports import RevisionStatusReport


def main():
    report = RevisionStatusReport().generate_report()
    slack_message(text=report)


if __name__ == '__main__':
    main()
