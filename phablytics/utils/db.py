# Python Standard Library Imports
import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def sqlite_do(db_name):
    """Context manager for SQLite

    References:
    - https://stackoverflow.com/a/67436763/865091
    - https://stackoverflow.com/a/65644970/865091
    """
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    yield cur
    conn.commit()
    conn.close()
