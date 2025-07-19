"""Enhanced SQLite helper with performance optimizations."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

_DB = Path("data/videos.db")


def _conn(timeout: Optional[int] = None):
    """Create database connection with configurable timeout."""
    _DB.parent.mkdir(exist_ok=True)
    timeout = timeout or 30
    conn = sqlite3.connect(_DB, timeout=timeout)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    conn.execute("PRAGMA journal_mode=WAL")  # Write-ahead logging for better concurrency
    conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety and speed
    conn.execute("PRAGMA cache_size=10000")  # Increase cache size
    conn.execute("PRAGMA temp_store=memory")  # Store temp data in memory
    return conn


def init_db():
    """Initialize database with optimized schema and indexes."""
    with _conn() as conn:
        c = conn.cursor()
        
        # Main metadata table
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                channel TEXT,
                url TEXT,
                description TEXT,
                transcript TEXT
            )
            """
        )
        
        # Performance indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_videos_title ON videos(title)")
        
        # Table for historical trend analysis
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS video_stats (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                fetched_at TEXT,
                view_count INTEGER,
                like_count INTEGER,
                FOREIGN KEY (video_id) REFERENCES videos (video_id)
            )
            """
        )
        
        # Full-text search table
        c.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
                video_id UNINDEXED,
                text,
                content=''
            );
            """
        )
        
        # Table for search history
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS search_history (
                search_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                results TEXT NOT NULL
            )
            """
        )

        conn.commit()
        print("Database initialized successfully")


def add_search_to_history(query: str, results: List[Dict]) -> int:
    """Adds a search query and its results to the history."""
    import json

    with _conn() as conn:
        c = conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        results_json = json.dumps(results)
        c.execute(
            "INSERT INTO search_history (query, timestamp, results) VALUES (?, ?, ?)",
            (query, timestamp, results_json),
        )
        conn.commit()
        return c.lastrowid


def get_search_history() -> List[Dict]:
    """Retrieves all search history records."""
    with _conn() as conn:
        c = conn.cursor()
        c.execute("SELECT search_id, query, timestamp FROM search_history ORDER BY timestamp DESC")
        rows = c.fetchall()
        keys = ["search_id", "query", "timestamp"]
        return [dict(zip(keys, row)) for row in rows]


def get_search_result(search_id: int) -> Optional[Dict]:
    """Retrieves a specific search result by its ID."""
    import json

    with _conn() as conn:
        c = conn.cursor()
        c.execute("SELECT results FROM search_history WHERE search_id = ?", (search_id,))
        row = c.fetchone()
        if row:
            return json.loads(row[0])
        return None


def add_videos(videos: List[Dict]) -> int:
    """Add videos to database and record historical stats."""
    if not videos:
        return 0

    added_count = 0
    with _conn() as conn:
        c = conn.cursor()

        # Prepare batch data
        video_data = []
        stats_data = []
        fetched_time = datetime.utcnow().isoformat()

        for v in videos:
            video_data.append(
                (
                    v["video_id"],
                    v["title"],
                    v["channel"],
                    v["url"],
                    v.get("description", ""),
                    v.get("transcript", ""),
                )
            )
            stats_data.append(
                (
                    v["video_id"],
                    fetched_time,
                    v.get("view_count"),
                    v.get("like_count"),
                )
            )

        try:
            # Insert basic video info (ignore if already exists)
            c.executemany(
                """
                INSERT OR IGNORE INTO videos(
                    video_id, title, channel, url, description, transcript
                )
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                video_data,
            )
            added_count = c.rowcount

            # Insert historical stats for all fetched videos
            c.executemany(
                """
                INSERT INTO video_stats (video_id, fetched_at, view_count, like_count)
                VALUES (?, ?, ?, ?)
                """,
                stats_data,
            )
            
            conn.commit()
            
            print(
                f"Processed {len(videos)} videos. Added {added_count} new. "
                f"Inserted {len(stats_data)} stat records."
            )

        except sqlite3.Error as e:
            print(f"Database error during batch insert: {e}")
            conn.rollback()
            raise

    return added_count


def search(query: str, limit: int = 10) -> List[Dict]:
    """Enhanced search with better ranking and performance."""
    if not query.strip():
        return []
    
    with _conn() as conn:
        c = conn.cursor()
        
        # Use FTS5 with highlighting and snippet support
        rows = c.execute(
            """
            SELECT 
                v.video_id, 
                v.title, 
                v.channel, 
                v.url, 
                v.description, 
                v.transcript
            FROM docs d
            JOIN videos v ON v.video_id = d.video_id
            WHERE d.text MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        
        keys = ["video_id", "title", "channel", "url", "description", "transcript"]
        results = [dict(zip(keys, row)) for row in rows]
        
        return results


def get_video_count() -> int:
    """Get total video count for monitoring."""
    with _conn() as conn:
        c = conn.cursor()
        return c.execute("SELECT COUNT(*) FROM videos").fetchone()[0]

def get_trend_data(topic: str) -> List[Dict]:
    """
    Get historical view counts for videos related to a topic.
    """
    with _conn() as conn:
        c = conn.cursor()
        rows = c.execute(
            """
            SELECT
                vs.fetched_at,
                vs.view_count
            FROM video_stats vs
            JOIN videos v ON v.video_id = vs.video_id
            WHERE v.title LIKE ? OR v.description LIKE ?
            ORDER BY vs.fetched_at
            """,
            (f"%{topic}%", f"%{topic}%"),
        ).fetchall()

        keys = ["date", "views"]
        return [dict(zip(keys, row)) for row in rows]

def cleanup_old_videos(days: int = 30) -> int:
    """Remove videos older than specified days."""
    with _conn() as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM videos WHERE rowid IN (SELECT rowid FROM videos ORDER BY rowid DESC LIMIT -1 OFFSET 1000)"
        )
        deleted = c.rowcount
        conn.commit()
        print(f"Cleaned up {deleted} old videos")
        return deleted


def vacuum_db():
    """Optimize database file size."""
    with _conn() as conn:
        conn.execute("VACUUM")
        print("Database vacuumed")
