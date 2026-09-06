import datetime

MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60

PREFIX = "GMT"
AHEAD = "+"
BEHIND = "-"


def now():
    return datetime.datetime.now()


def local_moment():
    return now().astimezone()


def utc_offset_minutes():
    offset = local_moment().utcoffset()

    if offset is None:
        return 0

    return int(offset.total_seconds() // SECONDS_PER_MINUTE)


def sign_of(minutes):
    if minutes < 0:
        return BEHIND

    return AHEAD


def formatted_offset(minutes):
    hours = abs(minutes) // MINUTES_PER_HOUR
    rest = abs(minutes) % MINUTES_PER_HOUR

    return f"{PREFIX}{sign_of(minutes)}{hours:02d}:{rest:02d}"


def described_offset():
    return formatted_offset(utc_offset_minutes())
