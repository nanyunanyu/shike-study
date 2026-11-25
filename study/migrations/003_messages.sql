CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('reminder','encouragement')),
    body TEXT NOT NULL CHECK (length(body) BETWEEN 1 AND 300),
    created_at INTEGER NOT NULL,
    due_at INTEGER NOT NULL,
    previewed_at INTEGER,
    read_at INTEGER
);
CREATE INDEX messages_inbox ON messages(recipient_id,due_at DESC,id DESC);
CREATE INDEX messages_unread ON messages(recipient_id,due_at DESC,id DESC) WHERE read_at IS NULL;
