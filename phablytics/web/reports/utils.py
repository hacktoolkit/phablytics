# Third Party (PyPI) Imports
from flask import url_for

# Phablytics Imports
from phablytics.settings import PHABLYTICS_BASE_URL


def get_report_url(report_name):
    if PHABLYTICS_BASE_URL:
        # TODO: make it work with url_for
        # https://flask.palletsprojects.com/en/1.1.x/api/#flask.url_for
        # url = '{}{}'.format(
        #     PHABLYTICS_BASE_URL,
        #     url_for('.show', report_name=report_name)
        # )
        url = '{}/reports/{}'.format(
            PHABLYTICS_BASE_URL,
            report_name
        )
    else:
        url = None
    return url
