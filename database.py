"""
database.py  —  SQLite helpers shared across modules.
"""

import sqlite3
import config


def get_conn():
    return sqlite3.connect(config.DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_ids (
                id TEXT PRIMARY KEY
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                source_id   TEXT PRIMARY KEY,
                type        TEXT,
                subreddit   TEXT,
                url         TEXT,
                title       TEXT,
                body        TEXT,
                author      TEXT,
                created_utc TEXT,
                status      TEXT DEFAULT 'pending',  -- pending | approved | rejected | posted | error
                reply_draft TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def already_seen(source_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM seen_ids WHERE id = ?", (source_id,)).fetchone()
        return row is not None


def mark_seen(source_id: str):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO seen_ids (id) VALUES (?)", (source_id,))
        conn.commit()


def save_post(item: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO posts
                (source_id, type, subreddit, url, title, body, author, created_utc)
            VALUES
                (:source_id, :type, :subreddit, :url, :title, :body, :author, :created_utc)
        """, item)
        conn.commit()


def update_status(source_id: str, status: str, reply_draft: str = None):
    with get_conn() as conn:
        if reply_draft is not None:
            conn.execute(
                "UPDATE posts SET status = ?, reply_draft = ? WHERE source_id = ?",
                (status, reply_draft, source_id)
            )
        else:
            conn.execute(
                "UPDATE posts SET status = ? WHERE source_id = ?",
                (status, source_id)
            )
        conn.commit()


def get_posts_by_status(status: str) -> list[dict]:
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM posts WHERE status = ?", (status,)
        ).fetchall()
        return [dict(r) for r in rows]
