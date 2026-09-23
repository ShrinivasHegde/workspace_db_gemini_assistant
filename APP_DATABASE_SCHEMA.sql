-- Run this against PostgreSQL database `analyse_db` if you want to create
-- application tables manually. The application runs this idempotent DDL at startup.
CREATE SCHEMA IF NOT EXISTS assistant;

CREATE TABLE IF NOT EXISTS assistant.chat_sessions (
    id BIGINT PRIMARY KEY,
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

CREATE INDEX IF NOT EXISTS ix_chat_sessions_updated_at ON assistant.chat_sessions (updated_at DESC);
CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id_id ON assistant.chat_messages (session_id, id);
