import json

from ..db.codec import normalize_review
from ..db.repositories import days as days_repo, focus as focus_repo


def has_review_content(review) -> bool:
    if not isinstance(review, dict):
        return False
    if review.get('mood') is not None or review.get('focus_score') is not None:
        return True
    if any(str(item).strip() for item in review.get('effective', [])):
        return True
    if any(str(item).strip() for item in review.get('priorities', [])):
        return True
    if review.get('issues'):
        return True
    return any(str(review.get(field, '')).strip() for field in ('other', 'adjustment', 'reflection'))


def list_reviews(
    db,
    uid: int,
    today: str,
    *,
    mood: str | None = None,
    issue: str | None = None,
    query: str | None = None,
    before: str | None = None,
    limit: int = 20,
) -> dict:
    focus_map = focus_repo.sum_by_date_up_to(db, uid, today)
    rows = days_repo.list_up_to(db, uid, today, descending=True)

    all_entries = []
    mood_counts: dict[str, int] = {}
    score_sum = 0
    score_count = 0

    for row in rows:
        review = normalize_review(json.loads(row['review']))
        if not has_review_content(review):
            continue
        if review['mood']:
            mood_counts[review['mood']] = mood_counts.get(review['mood'], 0) + 1
        if review['focus_score'] is not None:
            score_sum += review['focus_score']
            score_count += 1
        tasks = json.loads(row['tasks'])
        completed = sum(1 for t in tasks if t.get('done'))
        total = len(tasks)
        all_entries.append(
            dict(
                date=row['date'],
                checked_at=row['checked_at'],
                completed=completed,
                total=total,
                rate=completed / total if total else None,
                focus_seconds=focus_map.get(row['date'], 0),
                review=review,
            )
        )

    needle = (query or '').strip().lower()
    filtered = []
    for entry in all_entries:
        review = entry['review']
        if before and entry['date'] >= before:
            continue
        if mood and review['mood'] != mood:
            continue
        if issue and issue not in review['issues']:
            continue
        if needle:
            haystack = ' '.join(
                [
                    entry['date'],
                    *review['effective'],
                    *review['priorities'],
                    *review['issues'],
                    review['other'],
                    review['adjustment'],
                    review['reflection'],
                ]
            ).lower()
            if needle not in haystack:
                continue
        filtered.append(entry)

    page = filtered[:limit]
    next_before = page[-1]['date'] if len(filtered) > limit else None
    summary = dict(
        total_reviews=len(all_entries),
        avg_focus_score=round(score_sum / score_count, 1) if score_count else None,
        mood_counts=mood_counts,
    )
    return dict(items=page, next_before=next_before, summary=summary)
