CREATE TABLE timer_requests (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    id TEXT NOT NULL, date TEXT NOT NULL,
    PRIMARY KEY (user_id,id)
);
CREATE INDEX timer_requests_date ON timer_requests(date);
