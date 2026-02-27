"""Database layer for short drama rankings storage"""

import sqlite3
import os
from datetime import datetime, timedelta
from config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS dramas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crawl_time TEXT NOT NULL,
            platform TEXT NOT NULL,
            drama_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            theme TEXT,
            episode_count INTEGER,
            collect_count INTEGER,
            read_count INTEGER,
            like_count INTEGER,
            score REAL,
            rank INTEGER,
            cover_url TEXT,
            extra_json TEXT,
            UNIQUE(crawl_time, platform, drama_id)
        );

        CREATE INDEX IF NOT EXISTS idx_dramas_time
            ON dramas(crawl_time);
        CREATE INDEX IF NOT EXISTS idx_dramas_platform
            ON dramas(platform, crawl_time);
        CREATE INDEX IF NOT EXISTS idx_dramas_lookup
            ON dramas(platform, drama_id, crawl_time);

        CREATE TABLE IF NOT EXISTS crawl_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crawl_time TEXT NOT NULL,
            platform TEXT NOT NULL,
            count INTEGER NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            duration_sec REAL
        );
    """)
    conn.commit()
    conn.close()


def insert_dramas(crawl_time, platform, items):
    conn = get_db()
    conn.executemany("""
        INSERT OR REPLACE INTO dramas
        (crawl_time, platform, drama_id, title, description, theme,
         episode_count, collect_count, read_count, like_count, score, rank,
         cover_url, extra_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (crawl_time, platform,
         item['drama_id'], item['title'], item.get('description'),
         item.get('theme'), item.get('episode_count'),
         item.get('collect_count'), item.get('read_count'),
         item.get('like_count'), item.get('score'), item.get('rank'),
         item.get('cover_url'), item.get('extra_json'))
        for item in items
    ])
    conn.commit()
    conn.close()
    return len(items)


def log_crawl(crawl_time, platform, count, status, message=None, duration=None):
    conn = get_db()
    conn.execute("""
        INSERT INTO crawl_log (crawl_time, platform, count, status, message, duration_sec)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (crawl_time, platform, count, status, message, duration))
    conn.commit()
    conn.close()


def get_latest_crawl_time(platform=None):
    conn = get_db()
    if platform:
        row = conn.execute(
            "SELECT MAX(crawl_time) as t FROM dramas WHERE platform=?", (platform,)
        ).fetchone()
    else:
        row = conn.execute("SELECT MAX(crawl_time) as t FROM dramas").fetchone()
    conn.close()
    return row['t'] if row else None


def get_dramas_at(crawl_time, platform):
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM dramas
        WHERE crawl_time=? AND platform=?
        ORDER BY rank
    """, (crawl_time, platform)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_previous_crawl_time(current_time, platform=None):
    conn = get_db()
    if platform:
        row = conn.execute("""
            SELECT MAX(crawl_time) as t FROM dramas
            WHERE crawl_time < ? AND platform=?
        """, (current_time, platform)).fetchone()
    else:
        row = conn.execute("""
            SELECT MAX(crawl_time) as t FROM dramas WHERE crawl_time < ?
        """, (current_time,)).fetchone()
    conn.close()
    return row['t'] if row else None


def get_all_platforms_at(crawl_time):
    conn = get_db()
    rows = conn.execute("""
        SELECT DISTINCT platform FROM dramas WHERE crawl_time=?
    """, (crawl_time,)).fetchall()
    conn.close()
    return [r['platform'] for r in rows]


def get_drama_history(drama_id, platform, days=7):
    conn = get_db()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    rows = conn.execute("""
        SELECT crawl_time, rank, read_count, collect_count, score
        FROM dramas
        WHERE drama_id=? AND platform=? AND crawl_time>=?
        ORDER BY crawl_time
    """, (drama_id, platform, since)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_theme_stats(platform, crawl_time):
    conn = get_db()
    rows = conn.execute("""
        SELECT theme, COUNT(*) as count, AVG(rank) as avg_rank
        FROM dramas
        WHERE platform=? AND crawl_time=? AND theme IS NOT NULL
        GROUP BY theme
        ORDER BY count DESC
    """, (platform, crawl_time)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_crawl_times(days=7):
    conn = get_db()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    rows = conn.execute("""
        SELECT DISTINCT crawl_time FROM dramas
        WHERE crawl_time >= ?
        ORDER BY crawl_time
    """, (since,)).fetchall()
    conn.close()
    return [r['crawl_time'] for r in rows]


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
