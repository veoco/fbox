from datetime import datetime, timezone, timedelta


def get_now() -> datetime:
    tz = timezone(timedelta())
    now = datetime.now(tz)
    return now
