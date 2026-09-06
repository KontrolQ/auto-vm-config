import struct

from filesystems.directories import timestamps
from filesystems.naming import shortnames

ENTRY_SIZE = 32

READ_ONLY = 0x01
HIDDEN = 0x02
SYSTEM = 0x04
VOLUME_LABEL = 0x08
DIRECTORY = 0x10
ARCHIVE = 0x20
LONG_NAME_PART = READ_ONLY | HIDDEN | SYSTEM | VOLUME_LABEL

NAME_OFFSET = 0
ATTRIBUTES_OFFSET = 11
FINE_RESOLUTION_OFFSET = 13
CREATED_TIME_OFFSET = 14
CREATED_DATE_OFFSET = 16
ACCESSED_DATE_OFFSET = 18
CLUSTER_HIGH_OFFSET = 20
MODIFIED_TIME_OFFSET = 22
MODIFIED_DATE_OFFSET = 24
CLUSTER_LOW_OFFSET = 26
SIZE_OFFSET = 28

END_OF_DIRECTORY = 0x00
DELETED = 0xE5

SELF_NAME = b".          "
PARENT_NAME = b"..         "

HIGH_HALF_SHIFT = 16
HALF_MASK = 0xFFFF


def high_half_of(cluster):
    return (cluster >> HIGH_HALF_SHIFT) & HALF_MASK


def low_half_of(cluster):
    return cluster & HALF_MASK


def joined_halves(high, low):
    return (high << HIGH_HALF_SHIFT) | low


def build(name, attributes, first_cluster, size, moment):
    return with_raw_name(
        shortnames.packed(name), attributes, first_cluster, size, moment
    )


def with_raw_name(raw_name, attributes, first_cluster, size, moment):
    entry = bytearray(ENTRY_SIZE)

    entry[NAME_OFFSET : NAME_OFFSET + len(raw_name)] = raw_name
    entry[ATTRIBUTES_OFFSET] = attributes
    entry[FINE_RESOLUTION_OFFSET] = timestamps.packed_fine_resolution(moment)

    struct.pack_into(
        "<H", entry, CREATED_TIME_OFFSET, timestamps.packed_time(moment)
    )
    struct.pack_into(
        "<H", entry, CREATED_DATE_OFFSET, timestamps.packed_date(moment)
    )
    struct.pack_into(
        "<H", entry, ACCESSED_DATE_OFFSET, timestamps.packed_date(moment)
    )
    struct.pack_into(
        "<H", entry, MODIFIED_TIME_OFFSET, timestamps.packed_time(moment)
    )
    struct.pack_into(
        "<H", entry, MODIFIED_DATE_OFFSET, timestamps.packed_date(moment)
    )

    struct.pack_into("<H", entry, CLUSTER_HIGH_OFFSET, high_half_of(first_cluster))
    struct.pack_into("<H", entry, CLUSTER_LOW_OFFSET, low_half_of(first_cluster))
    struct.pack_into("<I", entry, SIZE_OFFSET, size)

    return bytes(entry)


def read(raw):
    return {
        "name": shortnames.unpacked(raw[NAME_OFFSET:ATTRIBUTES_OFFSET]),
        "attributes": raw[ATTRIBUTES_OFFSET],
        "first_cluster": joined_halves(
            struct.unpack_from("<H", raw, CLUSTER_HIGH_OFFSET)[0],
            struct.unpack_from("<H", raw, CLUSTER_LOW_OFFSET)[0],
        ),
        "size": struct.unpack_from("<I", raw, SIZE_OFFSET)[0],
        "modified_date": timestamps.unpacked_date(
            struct.unpack_from("<H", raw, MODIFIED_DATE_OFFSET)[0]
        ),
        "modified_time": timestamps.unpacked_time(
            struct.unpack_from("<H", raw, MODIFIED_TIME_OFFSET)[0]
        ),
    }


def ends_the_directory(raw):
    return raw[NAME_OFFSET] == END_OF_DIRECTORY


def is_deleted(raw):
    return raw[NAME_OFFSET] == DELETED


def is_long_name_part(raw):
    return raw[ATTRIBUTES_OFFSET] == LONG_NAME_PART


def is_volume_label(raw):
    return bool(raw[ATTRIBUTES_OFFSET] & VOLUME_LABEL)


def raw_name_of(raw):
    return raw[NAME_OFFSET : NAME_OFFSET + len(SELF_NAME)]


def is_self_or_parent(raw):
    return raw_name_of(raw) in (SELF_NAME, PARENT_NAME)


def holds_a_file(raw):
    return not (
        ends_the_directory(raw)
        or is_deleted(raw)
        or is_long_name_part(raw)
        or is_volume_label(raw)
        or is_self_or_parent(raw)
    )
