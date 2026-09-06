ENTRIES_KEY = "zone"

NAME = "name"
LABEL = "label"
OFFSET = "offset"
DAYLIGHT = "daylight"

NOTHING_MATCHES = None


def entries_in(document):
    return document.get(ENTRIES_KEY, [])


def at_offset(document, minutes):
    return [held for held in entries_in(document) if held[OFFSET] == minutes]


def steadiest(candidates):
    without_daylight = [held for held in candidates if not held[DAYLIGHT]]

    return (without_daylight or candidates)[0]


def for_offset(document, minutes):
    candidates = at_offset(document, minutes)

    if not candidates:
        return NOTHING_MATCHES

    return steadiest(candidates)[NAME]


def options_of(document):
    return [
        {"label": held[LABEL], "note": held[NAME], "value": held[NAME]}
        for held in entries_in(document)
    ]
