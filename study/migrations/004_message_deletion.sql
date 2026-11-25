ALTER TABLE messages ADD COLUMN recipient_deleted_at INTEGER;
DROP INDEX messages_unread;
CREATE INDEX messages_unread ON messages(recipient_id,due_at DESC,id DESC)
    WHERE read_at IS NULL AND recipient_deleted_at IS NULL;
CREATE INDEX messages_sent ON messages(sender_id,recipient_id,due_at DESC,id DESC);
