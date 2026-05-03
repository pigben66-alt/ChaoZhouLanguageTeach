import math
import uuid
from datetime import datetime, date


def paginate(page: int = 1, page_size: int = 20) -> tuple[int, int]:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    offset = (page - 1) * page_size
    return offset, page_size


def calc_total_pages(total: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size))


def safe_uuid(val: str | uuid.UUID | None) -> uuid.UUID | None:
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(val)
    except (ValueError, AttributeError):
        return None


def days_between(d1: datetime | date | None, d2: datetime | date | None) -> int:
    if d1 is None or d2 is None:
        return 0
    if isinstance(d1, datetime):
        d1 = d1.date()
    if isinstance(d2, datetime):
        d2 = d2.date()
    return (d2 - d1).days


def bkt_update(
    p_learned: float, p_transit: float, p_guess: float, p_slip: float, correct: bool
) -> float:
    if correct:
        p_correct_given_learned = 1 - p_slip
        p_correct_given_unlearned = p_guess
    else:
        p_correct_given_learned = p_slip
        p_correct_given_unlearned = 1 - p_guess

    p_evidence = p_learned * p_correct_given_learned + (1 - p_learned) * p_correct_given_unlearned
    if p_evidence == 0:
        return p_learned

    p_learned_new = (p_learned * p_correct_given_learned) / p_evidence
    p_learned_new = p_learned_new + (1 - p_learned_new) * p_transit
    return min(1.0, max(0.0, p_learned_new))


def sm2_update(ef_factor: float, quality: int, interval: int, repetitions: int) -> tuple[float, int]:
    if quality < 3:
        return ef_factor, 1

    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 6
    else:
        new_interval = round(interval * ef_factor)

    new_ef = ef_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)

    return new_ef, new_interval
