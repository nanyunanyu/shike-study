CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password TEXT NOT NULL, role TEXT NOT NULL CHECK (role IN ('admin','user')),
    active INTEGER NOT NULL DEFAULT 1, must_change INTEGER NOT NULL DEFAULT 0,
    failures INTEGER NOT NULL DEFAULT 0, lock_until INTEGER NOT NULL DEFAULT 0,
    preferences TEXT NOT NULL, categories TEXT NOT NULL
);
CREATE UNIQUE INDEX one_admin ON users(role) WHERE role='admin';
CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf TEXT NOT NULL, expires INTEGER NOT NULL
);
CREATE INDEX sessions_user ON sessions(user_id);
CREATE TABLE plans (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    id TEXT NOT NULL, date TEXT NOT NULL, created_at INTEGER NOT NULL, tasks TEXT NOT NULL,
    PRIMARY KEY (user_id,id)
);
CREATE INDEX plans_date ON plans(user_id,date DESC,created_at DESC);
CREATE TABLE days (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date TEXT NOT NULL, tasks TEXT NOT NULL, review TEXT NOT NULL, checked_at INTEGER,
    PRIMARY KEY (user_id,date)
);
CREATE TABLE timers (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    state TEXT NOT NULL
);
CREATE TABLE focus (
    user_id INTEGER NOT NULL, id TEXT NOT NULL, date TEXT NOT NULL,
    started_at INTEGER NOT NULL, ended_at INTEGER NOT NULL, seconds INTEGER NOT NULL CHECK(seconds > 0),
    mode TEXT NOT NULL, task TEXT,
    PRIMARY KEY (user_id,id), FOREIGN KEY (user_id,date) REFERENCES days(user_id,date) ON DELETE CASCADE
);
CREATE INDEX focus_date ON focus(user_id,date);
