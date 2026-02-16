"""数据库初始化"""

import sqlite3
from ._constants import DB_PATH


def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY, ts TEXT, zone TEXT, type TEXT, val REAL
            );
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY, ts TEXT, op TEXT, detail TEXT,
                who TEXT DEFAULT 'AI'
            );
        """)