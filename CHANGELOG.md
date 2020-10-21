# CHANGELOG

## v2.1.1 (2020-08-25)

- Use accordion component to show/collapse bugs
- Fix Maniphest __str__ representation
- fix MANIPHEST_STATUSES_CLOSED vs MANIPHEST_STATUSES_OPE

## v2.1.0 (2020-08-25)

- add metrics class and utils for generating metrics
- adds bugs report to metrics
- refactored get_maniphest_tasks functions to properly paginate
- moves markdown to requirements
- fixes an HTML revision status report formatting bug
- update README with release instructions

## v2.0.0 (2020-08-24)

- include [web] variant of phablytics
- include Flask in requirements_web.txt
- explicitly require minimum Python 3.0
- properly package *.html template files with distribution
- add HTML-formatted reports
- convert emoji aliases to unicode characters

## v1.0.2 (2020-08-17)

- handles paginated results for Maniphest search

## v1.0.1 (2020-08-06)

- filter out changes-planned, include needs-revision

## v1.0.0 (2020-08-04)

- adds new dataclass ReportConfig to configure how reports should run
- all reports now work with ReportConfig
- adds report_name setting, which is a higher-level object than report_type
- multiple reports (with different report_names) can have different configurations using the same report_type
- updates differential revision search to include statuses of accepted, changes-planned, needs-review
- switches -r from --report_type to --report_name
- all Slack messages now support customizing username and emoji
- isort everything (switching to multi-line combo imports)
- updated README with some basic Get Started instructions

## v0.4.0 (2020-08-04)

- split out reports into its own directory module and separate files

## v0.3.0 (2020-06-17)

- use python-dotenv to read in env
- use settings.py in cwd
- various bug fixes

## v0.2.0 (2020-01-26)

- added CLI mode

## v0.1.0 (2020-01-26)

- update README, add LICENSE and a bunch of other build-related files
