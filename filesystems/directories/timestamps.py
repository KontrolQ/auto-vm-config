EPOCH_YEAR = 1980

SECONDS_PER_TICK = 2
TENTHS_PER_SECOND = 10

YEAR_SHIFT = 9
MONTH_SHIFT = 5

HOUR_SHIFT = 11
MINUTE_SHIFT = 5

DAY_MASK = 0x1F
MONTH_MASK = 0x0F
YEAR_MASK = 0x7F

TICK_MASK = 0x1F
MINUTE_MASK = 0x3F
HOUR_MASK = 0x1F


def packed_date(moment):
    return ((moment.year - EPOCH_YEAR) << YEAR_SHIFT) | (moment.month << MONTH_SHIFT) | moment.day


def packed_time(moment):
    return (
        (moment.hour << HOUR_SHIFT)
        | (moment.minute << MINUTE_SHIFT)
        | (moment.second // SECONDS_PER_TICK)
    )


def packed_fine_resolution(moment):
    remainder_seconds = moment.second % SECONDS_PER_TICK

    return remainder_seconds * TENTHS_PER_SECOND + moment.microsecond // 100000


def unpacked_date(raw):
    return (
        ((raw >> YEAR_SHIFT) & YEAR_MASK) + EPOCH_YEAR,
        (raw >> MONTH_SHIFT) & MONTH_MASK,
        raw & DAY_MASK,
    )


def unpacked_time(raw):
    return (
        (raw >> HOUR_SHIFT) & HOUR_MASK,
        (raw >> MINUTE_SHIFT) & MINUTE_MASK,
        (raw & TICK_MASK) * SECONDS_PER_TICK,
    )
