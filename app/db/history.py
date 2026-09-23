"""PostgreSQL persistence for application-owned chat sessions and messages."""
import uuid

import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings
from app.exceptions import DatabaseConnectionError

DDL = """
CREATE SCHEMA IF NOT EXISTS assistant;

CREATE TABLE IF NOT EXISTS assistant.chat_sessions (
    id UUID PRIMARY KEY,
    title VARCHAR(120) NOT NULL DEFAULT 'New database chat',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assistant.chat_messages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES assistant.chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_sessions_updated_at
    ON assistant.chat_sessions (updated_at DESC);
CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id_id
    ON assistant.chat_messages (session_id, id);
"""


class HistoryStore:
    """Repository for application data; never use this for the target database."""

    def connect(self):
        if not settings.app_database_url:
            raise DatabaseConnectionError(
                "APP_DATABASE_URL is not configured. Add the application PostgreSQL URL to .env.local."
            )
        try:
            return psycopg2.connect(settings.app_database_url, cursor_factory=RealDictCursor)
        except psycopg2.Error as error:
            raise DatabaseConnectionError(f"Could not connect to the application database: {error}") from error

    def initialize(self):
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute(DDL)

    def create_session(self, title: str | None = None):
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO assistant.chat_sessions (id, title) VALUES (%s, %s)
                   RETURNING id::text, title, created_at, updated_at""",
                (str(uuid.uuid4()), title or "New database chat"),
            )
            return dict(cursor.fetchone())

    def get_session(self, session_id: str):
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT id::text, title, created_at, updated_at FROM assistant.chat_sessions WHERE id = %s", (session_id,))
            row = cursor.fetchone()
        return dict(row) if row else None

    def list_sessions(self):
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT id::text, title, created_at, updated_at FROM assistant.chat_sessions ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_session(self, session_id: str) -> bool:
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM assistant.chat_sessions WHERE id = %s", (session_id,))
            return cursor.rowcount > 0

    def messages(self, session_id: str):
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT id, role, content, created_at FROM assistant.chat_messages WHERE session_id = %s ORDER BY id", (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_message(self, session_id: str, role: str, content: str):
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO assistant.chat_messages (session_id, role, content)
                   VALUES (%s, %s, %s) RETURNING id, role, content, created_at""",
                (session_id, role, content),
            )
            message = dict(cursor.fetchone())
            cursor.execute(
                """UPDATE assistant.chat_sessions SET updated_at = NOW(),
                   title = CASE WHEN title = 'New database chat' AND %s = 'user'
                                THEN LEFT(%s, 80) ELSE title END WHERE id = %s""",
                (role, content, session_id),
            )
            return message
