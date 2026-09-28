"""
Achievement and XP engine.

Handles:
  - XP→level conversion
  - Event evaluation against achievement criteria
  - Unlock detection + XP rewards
"""
from django.conf import settings

from .models import Achievement, UserAchievement, UserXP

DEFAULT_EVENT_XP = settings.ACHIEVEMENT_EVENT_XP


def level_for_xp(xp: int) -> int:
    """Level from XP using a linear per-level cost."""
    per_level = settings.ACHIEVEMENT_XP_PER_LEVEL
    level = int(xp / per_level) + 1
    return min(level, settings.ACHIEVEMENT_MAX_LEVEL)


def xp_bounds(level: int) -> tuple[int, int]:
    """Return (level floor xp, needed xp to reach next level)."""
    per_level = settings.ACHIEVEMENT_XP_PER_LEVEL
    floor = max(0, (level - 1)) * per_level
    top = level * per_level
    return floor, top


def _criteria_matches(criteria: dict, event: dict) -> bool:
    """Does an achievement's criteria apply to this event's type?"""
    if not criteria:
        return False
    return criteria.get("event") == event.get("type")


def _apply_progress(current: int, criteria: dict, event: dict) -> int:
    """
    Increment progress for count-style achievements; for "peak" style
    achievements (value is an absolute rating/streak) take the max.
    """
    mode = criteria.get("mode", "count")
    actual = event.get("value", 1)
    if mode == "set":
        return max(current, int(actual))
    return current + int(actual or 1)


def _record_event_on_user(user_id: str, event: dict):
    """Evaluate one event: accumulate XP and update achievement progress."""
    unlocked = []

    event_type = event.get("type")
    xp_gain = event.get("xp", DEFAULT_EVENT_XP.get(event_type, 0))
    if xp_gain:
        user_xp, _ = UserXP.objects.get_or_create(user_id=user_id)
        user_xp.total_xp += xp_gain
        user_xp.level = level_for_xp(user_xp.total_xp)
        user_xp.save(update_fields=["total_xp", "level", "updated_at"])

    candidates = Achievement.objects.filter(is_active=True)
    for achievement in candidates:
        criteria = achievement.criteria

        if not _criteria_matches(criteria, event):
            continue

        user_ach, _ = UserAchievement.objects.get_or_create(
            user_id=user_id, achievement=achievement
        )

        # Skip already-unlocked achievements
        if user_ach.unlocked_at is not None:
            continue

        new_progress = _apply_progress(user_ach.progress, criteria, event)
        target = criteria.get("value", 1)

        if new_progress >= target:
            user_ach.progress = target
            user_ach.unlocked_at = timezone_now()
            user_ach.save(update_fields=["progress", "unlocked_at", "updated_at"])
            unlocked.append(achievement)

            # Grant the XP reward for the achievement itself
        else:
            user_ach.progress = new_progress
            user_ach.save(update_fields=["progress", "updated_at"])

    if unlocked:
        reward = sum(a.xp_reward for a in unlocked)
        if reward:
            user_xp, _ = UserXP.objects.get_or_create(user_id=user_id)
            user_xp.total_xp += reward
            user_xp.level = level_for_xp(user_xp.total_xp)
            user_xp.save(update_fields=["total_xp", "level", "updated_at"])

    return unlocked


def handle_event(user_id: str, event: dict) -> dict:
    """
    Public entry point used by the API layer and Celery tasks.

    :returns: {"unlocked": [codes...], "xp_gained": int}
    """
    if not event or not event.get("type"):
        return {"unlocked": [], "xp_gained": 0}

    before = 0
    stored = UserXP.objects.filter(user_id=user_id).first()
    if stored:
        before = stored.total_xp

    unlocked = _record_event_on_user(user_id, event)

    xp_now = UserXP.objects.filter(user_id=user_id).values_list("total_xp", flat=True).first() or 0
    return {
        "unlocked": [a.code for a in unlocked],
        "xp_gained": xp_now - before,
        "total_xp": xp_now,
    }


def timezone_now():
    from django.utils import timezone

    return timezone.now()