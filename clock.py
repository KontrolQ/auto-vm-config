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
    return "%s%s%02d:%02d" % (
        PREFIX,
        sign_of(minutes),
        abs(minutes) // MINUTES_PER_HOUR,
        abs(minutes) % MINUTES_PER_HOUR,
    )


def described_offset():
    return formatted_offset(utc_offset_minutes())
