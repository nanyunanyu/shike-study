import json

from ..db.repositories import sessions as sessions_repo, timers as timers_repo, users as users_repo
from . import timer as timer_service


def run_maintenance(store, timestamp: int) -> None:
    with store.transaction(write=True) as db:
        sessions_repo.purge_expired(db, timestamp)
        timers_repo.purge_old_requests(db, store.date(timestamp).isoformat())
        for row in timers_repo.list_all(db):
            timer_service.settle(db, row['user_id'], json.loads(row['state']), timestamp)
        initialized = users_repo.has_admin(db)
    if not initialized:
        return
    store.snapshot(timestamp)
