"""
Système de mémoire multi-niveaux pour BARBATOS :
1. Mémoire court terme (tampon de contexte de travail)
2. Mémoire long terme persistant (SQLite pour faits, préférences, historique et état persistant)
"""

import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional


class ShortTermMemory:
    """Tampon de mémoire de travail pour la session active."""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.messages: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, tool_calls: Optional[Any] = None):
        self.messages.append({
            "role": role,
            "content": content,
            "tool_calls": tool_calls,
            "timestamp": time.time(),
        })
        # Garde seulement les derniers max_turns messages
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-self.max_turns * 2:]

    def get_context(self) -> List[Dict[str, Any]]:
        return list(self.messages)

    def clear(self):
        self.messages.clear()


class LongTermMemory:
    """Mémoire persistante stockée dans SQLite."""

    def __init__(self, db_path: str = "data/barbatos_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table des faits & préférences apprises
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at REAL,
                    updated_at REAL
                )
            """)
            # Table des conversations passées
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL
                )
            """)
            # Table des tâches exécutées
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details_json TEXT,
                    created_at REAL
                )
            """)
            conn.commit()

    def remember_fact(self, key: str, value: str, category: str = "general"):
        """Enregistre ou met à jour une information apprise."""
        now = time.time()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO facts (key, value, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    category = excluded.category,
                    updated_at = excluded.updated_at
            """, (key.lower().strip(), value, category, now, now))
            conn.commit()

    def recall_fact(self, key: str) -> Optional[str]:
        """Récupère un fait par sa clé exacte."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT value FROM facts WHERE key = ?", (key.lower().strip(),)).fetchone()
            return row["value"] if row else None

    def search_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche des faits par mot-clé."""
        pattern = f"%{query.lower().strip()}%"
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT key, value, category FROM facts
                WHERE key LIKE ? OR value LIKE ?
                LIMIT ?
            """, (pattern, pattern, limit)).fetchall()
            return [dict(r) for r in rows]

    def log_conversation(self, session_id: str, role: str, content: str):
        """Historise un message dans la base."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO conversation_history (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, time.time()))
            conn.commit()

    def log_task(self, goal: str, status: str, details: Optional[Dict[str, Any]] = None, task_id: str = ""):
        """Historise une exécution de tâche."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO task_log (task_id, goal, status, details_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (task_id, goal, status, json.dumps(details or {}, ensure_ascii=False), time.time()))
            conn.commit()


# Instance globale
short_term_memory = ShortTermMemory()
long_term_memory = LongTermMemory()
