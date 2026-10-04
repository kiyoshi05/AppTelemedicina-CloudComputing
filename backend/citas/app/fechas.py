import os
from datetime import date, datetime, timedelta, timezone

# Perú está en UTC-5 todo el año. El servidor en AWS usa UTC.
ZONA = timezone(timedelta(hours=int(os.getenv("TZ_OFFSET_HOURS", "-5"))))


def hoy() -> date:
    return datetime.now(ZONA).date()
