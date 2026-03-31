import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

class DatabaseManager:
    def __init__(self, db_path: str = "medrec.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    audio_path TEXT,
                    transcript TEXT,
                    summary TEXT,
                    patient_id TEXT,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    field TEXT,
                    original_content TEXT,
                    edited_content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(uuid)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS physician_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    physician_id TEXT DEFAULT 'default',
                    category TEXT,
                    preference_key TEXT,
                    preference_value TEXT,
                    confidence REAL DEFAULT 0.5,
                    learned_from INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_uuid ON sessions(uuid)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pref_unique ON physician_preferences(physician_id, category, preference_key)")
            # Migration: add label column if missing
            try:
                conn.execute("ALTER TABLE sessions ADD COLUMN label TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # column already exists
            conn.commit()

    def add_session(self, uuid: str, audio_path: str, transcript: str, summary: str, metadata: Dict = None):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (uuid, audio_path, transcript, summary, metadata) VALUES (?, ?, ?, ?, ?)",
                (uuid, audio_path, transcript, summary, json.dumps(metadata or {}))
            )
            conn.commit()

    def update_session(self, uuid: str, transcript: str = None, summary: str = None):
        with self._get_connection() as conn:
            if transcript is not None:
                conn.execute("UPDATE sessions SET transcript = ? WHERE uuid = ?", (transcript, uuid))
            if summary is not None:
                conn.execute("UPDATE sessions SET summary = ? WHERE uuid = ?", (summary, uuid))
            conn.commit()

    def update_session_label(self, uuid: str, label: str):
        with self._get_connection() as conn:
            conn.execute("UPDATE sessions SET label = ? WHERE uuid = ?", (label, uuid))
            conn.commit()

    def add_feedback(self, session_id: str, field: str, original: str, edited: str):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO feedback (session_id, field, original_content, edited_content) VALUES (?, ?, ?, ?)",
                (session_id, field, original, edited)
            )
            conn.commit()

    def list_sessions(self) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_session(self, uuid: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM sessions WHERE uuid = ?", (uuid,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_session(self, uuid: str):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM feedback WHERE session_id = ?", (uuid,))
            conn.execute("DELETE FROM sessions WHERE uuid = ?", (uuid,))
            conn.commit()

    # ── Physician Preference Learning ────────────────────────────────

    def upsert_preference(self, category: str, key: str, value: str,
                          physician_id: str = "default") -> None:
        """Insert or update a learned preference, boosting confidence on repeat."""
        with self._get_connection() as conn:
            existing = conn.execute(
                "SELECT id, confidence, learned_from FROM physician_preferences "
                "WHERE physician_id = ? AND category = ? AND preference_key = ?",
                (physician_id, category, key)
            ).fetchone()

            if existing:
                new_conf = min(1.0, existing[1] + 0.1)  # cap at 1.0
                conn.execute(
                    "UPDATE physician_preferences "
                    "SET preference_value = ?, confidence = ?, learned_from = ?, updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = ?",
                    (value, new_conf, existing[2] + 1, existing[0])
                )
            else:
                conn.execute(
                    "INSERT INTO physician_preferences "
                    "(physician_id, category, preference_key, preference_value) VALUES (?, ?, ?, ?)",
                    (physician_id, category, key, value)
                )
            conn.commit()

    def get_preferences(self, physician_id: str = "default",
                        min_confidence: float = 0.0) -> List[Dict]:
        """Return all preferences above the confidence threshold."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT category, preference_key, preference_value, confidence, learned_from "
                "FROM physician_preferences "
                "WHERE physician_id = ? AND confidence >= ? "
                "ORDER BY confidence DESC",
                (physician_id, min_confidence)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_preference_prompt(self, physician_id: str = "default") -> str:
        """Format learned preferences as a prompt injection string."""
        prefs = self.get_preferences(physician_id, min_confidence=0.5)
        if not prefs:
            return ""
        lines = ["### PHYSICIAN STYLE PREFERENCES (learned from your corrections):"]
        for p in prefs:
            lines.append(f"- [{p['category']}] {p['preference_key']}: {p['preference_value']} "
                         f"(confidence: {p['confidence']:.0%}, from {p['learned_from']} corrections)")
        return "\n".join(lines)

    def get_feedback_count(self, physician_id: str = "default") -> int:
        """Return total number of feedback corrections."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM feedback")
            return cursor.fetchone()[0]

    def reset_preferences(self, physician_id: str = "default") -> int:
        """Delete all learned preferences. Returns count deleted."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM physician_preferences WHERE physician_id = ?",
                (physician_id,)
            )
            conn.commit()
            return cursor.rowcount
