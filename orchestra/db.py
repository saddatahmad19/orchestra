import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS tasks (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, prompt TEXT NOT NULL, engine TEXT NOT NULL,
 project_path TEXT, status TEXT NOT NULL CHECK(status IN
 ('pending_approval','queued','running','succeeded','failed','cancelled')),
 approval_required INTEGER NOT NULL DEFAULT 1, approved_by TEXT, worker_id TEXT,
 lease_until REAL, attempt INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 2,
 result TEXT, error TEXT, created_at REAL NOT NULL, updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status,created_at);
CREATE TABLE IF NOT EXISTS workers (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, hostname TEXT, platform TEXT,
 capabilities TEXT NOT NULL DEFAULT '[]', last_seen REAL NOT NULL, status TEXT NOT NULL DEFAULT 'online'
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, worker_id TEXT,
 kind TEXT NOT NULL, message TEXT NOT NULL, created_at REAL NOT NULL,
 FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
"""

class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=10000")
        try:
            yield conn
        finally:
            conn.close()
