"""SQLite state management for agent sessions."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiosqlite


class StateManager:
    """Manages SQLite state for agent sessions."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".graphitee" / "sessions.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path_str = str(self.db_path)
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._db_path_str)
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._create_tables()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _create_tables(self) -> None:
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS concept_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                concept_name TEXT NOT NULL,
                explored BOOLEAN DEFAULT FALSE,
                confidence REAL,
                first_mentioned_at TIMESTAMP,
                explored_at TIMESTAMP,
                UNIQUE(session_id, concept_name)
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role TEXT CHECK(role IN ('user', 'assistant', 'system')) NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                tool_name TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS article_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                content_json TEXT NOT NULL,
                tier INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                graph_json TEXT NOT NULL,
                tier INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_concept_session ON concept_states(session_id, concept_name)"
        )
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)"
        )
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tools_session ON tool_executions(session_id)"
        )

        await self._conn.commit()

    async def create_session(self, url: str, title: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        await self._conn.execute(
            "INSERT INTO sessions (id, url, title) VALUES (?, ?, ?)",
            (session_id, url, title),
        )
        await self._conn.commit()
        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        async with self._conn.execute(
            "SELECT id, url, title, created_at, updated_at FROM sessions WHERE id = ?",
            (session_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "url": row[1],
                    "title": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                }
            return None

    async def list_sessions(self) -> list[dict]:
        async with self._conn.execute(
            "SELECT id, url, title, created_at FROM sessions ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {"id": r[0], "url": r[1], "title": r[2], "created_at": r[3]}
                for r in rows
            ]

    async def add_message(self, session_id: str, role: str, content: str) -> int:
        await self._conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        await self._conn.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,),
        )
        await self._conn.commit()
        async with self._conn.execute("SELECT last_insert_rowid()") as cursor:
            return (await cursor.fetchone())[0]

    async def get_conversation_history(
        self, session_id: str, limit: int = 20
    ) -> list[dict]:
        async with self._conn.execute(
            """SELECT role, content, timestamp FROM messages 
               WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?""",
            (session_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {"role": r[0], "content": r[1], "timestamp": r[2]}
                for r in reversed(rows)
            ]

    async def update_concept_state(
        self,
        session_id: str,
        concept_name: str,
        explored: bool = True,
        confidence: Optional[float] = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        await self._conn.execute(
            """
            INSERT INTO concept_states (session_id, concept_name, explored, confidence, first_mentioned_at, explored_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, concept_name) DO UPDATE SET
                explored = excluded.explored,
                confidence = COALESCE(excluded.confidence, concept_states.confidence),
                explored_at = CASE WHEN excluded.explored THEN excluded.explored_at ELSE concept_states.explored_at END
        """,
            (
                session_id,
                concept_name,
                explored,
                confidence,
                now,
                now if explored else None,
            ),
        )
        await self._conn.commit()

    async def get_concept_states(
        self, session_id: str, explored: Optional[bool] = None
    ) -> list[dict]:
        query = "SELECT concept_name, explored, confidence, explored_at FROM concept_states WHERE session_id = ?"
        params = [session_id]
        if explored is not None:
            query += " AND explored = ?"
            params.append(explored)

        async with self._conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "concept_name": r[0],
                    "explored": r[1],
                    "confidence": r[2],
                    "explored_at": r[3],
                }
                for r in rows
            ]

    async def get_explored_concepts(self, session_id: str) -> set[str]:
        async with self._conn.execute(
            "SELECT concept_name FROM concept_states WHERE session_id = ? AND explored = TRUE",
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return {r[0] for r in rows}

    async def get_unexplored_concepts(self, session_id: str) -> set[str]:
        async with self._conn.execute(
            "SELECT concept_name FROM concept_states WHERE session_id = ? AND explored = FALSE",
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return {r[0] for r in rows}

    async def add_tool_execution(
        self, session_id: str, tool_name: str, input_data: Any, output_data: Any
    ) -> None:
        await self._conn.execute(
            """INSERT INTO tool_executions (session_id, tool_name, input_data, output_data) 
               VALUES (?, ?, ?, ?)""",
            (session_id, tool_name, json.dumps(input_data), json.dumps(output_data)),
        )
        await self._conn.commit()

    async def save_article_content(
        self, session_id: str, content: dict, tier: int = 1
    ) -> None:
        await self._conn.execute(
            "INSERT INTO article_content (session_id, content_json, tier) VALUES (?, ?, ?)",
            (session_id, json.dumps(content), tier),
        )
        await self._conn.commit()

    async def get_article_content(
        self, session_id: str, tier: Optional[int] = None
    ) -> Optional[dict]:
        query = "SELECT content_json FROM article_content WHERE session_id = ?"
        params = [session_id]
        if tier is not None:
            query += " AND tier = ?"
            params.append(tier)
        query += " ORDER BY created_at DESC LIMIT 1"

        async with self._conn.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

    async def save_knowledge_graph(
        self, session_id: str, graph: dict, tier: int = 1
    ) -> None:
        await self._conn.execute(
            "INSERT INTO knowledge_graph (session_id, graph_json, tier) VALUES (?, ?, ?)",
            (session_id, json.dumps(graph), tier),
        )
        await self._conn.commit()

    async def get_knowledge_graph(
        self, session_id: str, tier: Optional[int] = None
    ) -> Optional[dict]:
        query = "SELECT graph_json FROM knowledge_graph WHERE session_id = ?"
        params = [session_id]
        if tier is not None:
            query += " AND tier = ?"
            params.append(tier)
        query += " ORDER BY created_at DESC LIMIT 1"

        async with self._conn.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

    async def delete_session(self, session_id: str) -> None:
        await self._conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await self._conn.commit()

    async def __aenter__(self) -> "StateManager":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
