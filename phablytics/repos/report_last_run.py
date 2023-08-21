# Python Standard Library Imports
import math
import sqlite3
import time

# Phablytics Imports
from phablytics.utils.db import sqlite_do


class ReportLastRunRepo:
    DB_FILE = 'phablytics.sqlite'
    TABLE_NAME = 'reports_last_run'

    def __init__(self):
        with sqlite_do(self.DB_FILE) as cur:
            cur.execute(f"""CREATE TABLE IF NOT EXISTS {self.TABLE_NAME}(report_name VARCHAR PRIMARY KEY, timestamp INTEGER)""")

    def save_last_run(self, report_name):
        t = math.floor(time.time())

        with sqlite_do(self.DB_FILE) as cur:
            cur.execute(
                f"""INSERT INTO {self.TABLE_NAME} (report_name, timestamp)
VALUES('{report_name}', {t})
ON CONFLICT(report_name)
DO UPDATE SET timestamp={t};
"""
            )

    def get_last_run(self, report_name):
        with sqlite_do(self.DB_FILE) as cur:
            res = cur.execute(
                f"""SELECT timestamp FROM {self.TABLE_NAME} WHERE report_name = '{report_name}';
"""
            )
            row = res.fetchone()
            last_run = row[0] if row else None

        return last_run


report_last_run_repo = ReportLastRunRepo()
