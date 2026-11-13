-- Run this once in your PostgreSQL database if you want to initialize it manually.
-- FamEase stores the existing users + expenses JSON structure in one
-- persistent PostgreSQL row so the current Flask routes remain compatible.

CREATE TABLE IF NOT EXISTS famease_app_state (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO famease_app_state (id, payload)
VALUES (1, '{"users": {}, "user_expenses": {}, "expenses": []}'::jsonb)
ON CONFLICT (id) DO NOTHING;
