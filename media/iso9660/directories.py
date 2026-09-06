from media.iso9660 import records
from media.iso9660 import sectors

SEPARATORS = "/\\"

END_OF_RECORDS = 0


def components_of(path):
    wanted = path

    for separator in SEPARATORS:
        wanted = wanted.replace(separator, SEPARATORS[0])

    return [component for component in wanted.split(SEPARATORS[0]) if component]


def next_sector_boundary(position):
    return ((position // sectors.SECTOR_SIZE) + 1) * sectors.SECTOR_SIZE


def records_in(extent):
    found = []
    position = 0

    while position < len(extent):
        if records.length_of(extent, position) == END_OF_RECORDS:
            position = next_sector_boundary(position)
            continue

        found.append(records.sized(extent, position))
        position += records.length_of(extent, position)

    return found


def extent_of(handle, record):
    return sectors.span(
        handle, records.extent_of(record), records.data_length_of(record)
    )


def children_of(handle, record):
    return [
        child
        for child in records_in(extent_of(handle, record))
        if not records.is_special(child)
    ]


def named(children, wanted):
    for child in children:
        if records.name_of(child).upper() == wanted.upper():
            return child

    return None


def descended(handle, record, component):
    return named(children_of(handle, record), component)


def located(handle, root, path):
    record = root

    for component in components_of(path):
        if record is None or not records.is_directory(record):
            return None

        record = descended(handle, record, component)

    return record


def listed(handle, record):
    return [records.read(child) for child in children_of(handle, record)]
