"""SQLite connections are scoped to the Flask application context."""
import sqlite3
from flask import current_app, g

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE, password_hash TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sets (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), title TEXT NOT NULL,
 description TEXT NOT NULL, topic TEXT NOT NULL, visibility TEXT NOT NULL,
 version INTEGER NOT NULL, questions TEXT NOT NULL, updated_at TEXT NOT NULL, source_set_id TEXT
);
CREATE TABLE IF NOT EXISTS bookmarks (
 user_id TEXT NOT NULL REFERENCES users(id), set_id TEXT NOT NULL REFERENCES sets(id) ON DELETE CASCADE,
 PRIMARY KEY(user_id, set_id)
);
CREATE TABLE IF NOT EXISTS attempts (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), snapshot TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS sets_owner ON sets(owner_id);
CREATE INDEX IF NOT EXISTS attempts_user ON attempts(user_id);
'''


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=15)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute('PRAGMA journal_mode = WAL')
    db.executescript(SCHEMA)
    from seed import seed_database
    seed_database(db)
