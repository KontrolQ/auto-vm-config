from filesystems.directories import entries
from filesystems.fat12 import layout
from filesystems.naming import shortnames


def positions(parameters):
    return range(parameters["root_entries"])


def offset_of(parameters, position):
    return layout.offset_of_sector(
        parameters, layout.first_root_sector(parameters)
    ) + position * entries.ENTRY_SIZE


def slot(image, parameters, position):
    at = offset_of(parameters, position)

    return bytes(image[at : at + entries.ENTRY_SIZE])


def place(image, parameters, position, raw):
    at = offset_of(parameters, position)

    image[at : at + entries.ENTRY_SIZE] = raw


def occupied_positions(image, parameters):
    found = []

    for position in positions(parameters):
        raw = slot(image, parameters, position)

        if entries.ends_the_directory(raw):
            break

        if entries.holds_a_file(raw):
            found.append(position)

    return found


def names(image, parameters):
    return [
        entries.read(slot(image, parameters, position))["name"]
        for position in occupied_positions(image, parameters)
    ]


def matches(raw, name):
    return raw[: shortnames.PACKED_LENGTH] == shortnames.packed(name)


def position_of(image, parameters, name):
    for position in occupied_positions(image, parameters):
        if matches(slot(image, parameters, position), name):
            return position

    return None


def is_available(raw):
    return entries.ends_the_directory(raw) or entries.is_deleted(raw)


def first_available_position(image, parameters):
    for position in positions(parameters):
        if is_available(slot(image, parameters, position)):
            return position

    return None


def refuse_when_full(position):
    if position is None:
        raise ValueError("the root directory holds no more entries")


def add(image, parameters, raw):
    position = first_available_position(image, parameters)

    refuse_when_full(position)
    place(image, parameters, position, raw)

    return position


def remove(image, parameters, position):
    raw = bytearray(slot(image, parameters, position))
    raw[0] = entries.DELETED

    place(image, parameters, position, bytes(raw))
