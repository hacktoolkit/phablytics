# CHANGELOG

## v3.1.2 (2022-05-21)
- Fixes breadcrumbs for report names by preserving case

## v3.1.1 (2021-12-13)
- Removes an incorrect type hint

## v3.1.0 (2021-12-13)
- Fixes metric aggregation by customer, service, and owner (#12)
- Fixes `start_of_month` by simply using `1`, instead of `calendar.monthrange[0]`, (#11)
- Minor improvements to metrics explorer (#10)
- adds `CUSTOM_STATIC_DIR` and `CUSTOM_STYLESHEETS` served by `{{ url_for('custom_static', filename=filename) }}` (#9)

## v3.0.1 (2021-04-06)
- Include all open Maniphest statuses for upcoming tasks due report
  - awaitingbusiness
  - inprogress
  - open
  - stalled

## v3.0.0 (2020-12-22)
- added Explore page and blueprint
- adds mechanism to retrieve a list of Customers (special Project tag)
- adds the ability to filter task metrics by Customer
- styling for applied filters string
- formatting for task metrics
- adds custom segments (including nested segments) for projects on explore page
- filter by bulk project names
- add hyperlinks with quarter interval to explore
- slightly improved interval calculation
- improved section headings indicating interval
- adds aggregated metrics, normalized metrics and rate metrics
- tasks by project_phids query use AND, so need to make multiple queries
- display 2 decimal points
- adds AggregatedTaskMetricsStats as companion to TaskMetricsStats
- segment tasks by customer, users, and service
- move/refactor utils.py and constants.py into module with submodules
- add checks for null projects

## v2.7.0 (2020-11-19)
- adds statistical analysis

## v2.6.0 (2020-11-19)
- Version bump only

## v2.5.0 (2020-11-18)
- adds Stories, Features, Tasks in addition to Bugs as metric types

## v2.4.0 (2020-11-18)
- adds filters to web metrics
- adds the ability to select interval: week/month
- adds the ability to set custom start and end period

## v2.3.0 (2020-11-18)
- Adds breadcrumbs to website

## v2.2.1 (2020-11-04)
- Adds report setting: non_group_reviewer_acceptance_threshold
- Allows requiring a minimum number of acceptances by non-group reviewers for GroupReviewStatusReport

## v2.2.0 (2020-10-27)
- Adds GroupReviewStatusReport
- adds web link for RevisionStatusReport and GroupsReviewStatusReport
- convert REPORTS config from dict to list

## v2.1.2 (2020-10-21)
- update Maniphest open, closed statuses
- fix BugMetric namedtuple name

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
