DATE_FORMAT_YMD = '%Y-%m-%d'
DATE_FORMAT_MDY_SHORT = '%b %d, %Y'

INTERVAL_OPTIONS = [
    'week',
    'month',
    'quarter',
]
DEFAULT_INTERVAL_OPTION = 'week'

INTERVAL_DAYS_MAP = {
    'week': 7,
    'month': 30,
    'quarter': 90,
}
DEFAULT_INTERVAL_DAYS = INTERVAL_DAYS_MAP[DEFAULT_INTERVAL_OPTION]
