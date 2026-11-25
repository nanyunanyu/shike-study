CREATE TABLE message_dispatches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    recipient_count INTEGER NOT NULL,
    UNIQUE (sender_id, request_id)
);
ALTER TABLE messages ADD COLUMN dispatch_id INTEGER REFERENCES message_dispatches(id) ON DELETE CASCADE;
ALTER TABLE messages ADD COLUMN canceled_at INTEGER;
CREATE INDEX messages_dispatch ON messages(dispatch_id,recipient_id);
CREATE INDEX messages_admin_due ON messages(sender_id,due_at,id);
