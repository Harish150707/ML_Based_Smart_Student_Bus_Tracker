"""
database.py
Centralized MySQL connection handling for the Smart Student Tracking System.

Why this file exists
---------------------
The old code opened a single global `db` connection at import time and reused
it for the lifetime of the Flask process, while a couple of routes ALSO opened
their own separate `mysql.connector.connect(...)` with credentials copy-pasted
in multiple places. Two problems with that:

1. MySQL drops idle connections after a timeout (often just a few hours on
   default config). A long-lived global connection WILL die mid-session,
   and every route using it will start throwing
   "MySQL server has gone away" — usually right when you don't want it to
   (e.g. during your project demo).

2. Hardcoded credentials duplicated across the codebase are a pain to
   rotate and a security smell if the code is ever shared/committed.

This module fixes both: every request grabs a fresh, valid connection from a
pool and returns it when done. Credentials come from environment variables
with safe fallbacks, so nothing breaks if you haven't set them yet.

Usage in app.py
----------------
    from database import get_db_connection

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students")
        rows = cursor.fetchall()
        cursor.close()
    finally:
        conn.close()   # returns the connection to the pool, does NOT destroy it

Setting real credentials (recommended before you deploy/share this project)
-----------------------------------------------------------------------------
Windows (PowerShell), run once per session or add to your system env vars:
    $env:DB_HOST="localhost"
    $env:DB_USER="root"
    $env:DB_PASSWORD="your_real_password"
    $env:DB_NAME="smart_student_tracker"

If you don't set these, the fallbacks below (matching your current setup)
are used automatically.
"""

import os
import mysql.connector
from mysql.connector import pooling

DB_CONFIG= mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

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

    ALWAYS close() it when you're done (use try/finally, as shown above).
    close() returns the connection to the pool for reuse — it does not
    actually disconnect, so this is cheap to call on every request.
    """
    try:
        return _get_pool().get_connection()
    except mysql.connector.Error as err:
        raise RuntimeError(f"Database connection failed: {err}") from err
