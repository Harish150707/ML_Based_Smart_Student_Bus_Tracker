"""
database.py
Centralized MySQL connection handling for the Smart Student Tracking System.

FIX: DB_CONFIG must be a plain dict of connection settings — passing it to
MySQLConnectionPool via **DB_CONFIG unpacks it into keyword arguments
(host=..., user=..., etc). A previous version accidentally set DB_CONFIG to
the result of mysql.connector.connect(...), which returns a live connection
OBJECT, not a dict — that object can't be unpacked with **, which is exactly
the TypeError seen in production: "argument after ** must be a mapping, not
MySQLConnection".
"""

import os
import mysql.connector
from mysql.connector import pooling

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "Harish1507@"),
    "database": os.environ.get("DB_NAME", "smart_student_tracker"),
}

_pool = None


def _get_pool():
    """Lazily create the connection pool on first use."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="sst_pool",
            pool_size=10,
            pool_reset_session=True,
            **DB_CONFIG,
        )
    return _pool


def get_db_connection():
    """
    Returns a live connection borrowed from the pool.
    Always close() it when you're done (use try/finally).
    """
    try:
        return _get_pool().get_connection()
    except mysql.connector.Error as err:
        raise RuntimeError(f"Database connection failed: {err}") from err
