import sqlite3
from config import DATABASE_PATH


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS posted_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                model_id TEXT NOT NULL,
                title TEXT,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, model_id)
            )
        """)
        self.conn.commit()

    def is_posted(self, source: str, model_id: str) -> bool:
        cur = self.conn.execute(
            "SELECT id FROM posted_models WHERE source=? AND model_id=?",
            (source, model_id),
        )
        return cur.fetchone() is not None

    def mark_posted(self, source: str, model_id: str, title: str):
        self.conn.execute(
            "INSERT OR IGNORE INTO posted_models (source, model_id, title) VALUES (?, ?, ?)",
            (source, model_id, title),
        )
        self.conn.commit()

    def get_stats(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM posted_models")
        return cur.fetchone()[0]
