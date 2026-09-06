import struct

from partitioning import entries

RECORD_SIZE = 512

TABLE_OFFSET = 446
ENTRIES_AVAILABLE = 4

SIGNATURE_OFFSET = 510
SIGNATURE = 0xAA55


def refuse_more_than_the_table_holds(table):
    if len(table) > ENTRIES_AVAILABLE:
        raise ValueError(
            "a master boot record holds %d entries, not %d"
            % (ENTRIES_AVAILABLE, len(table))
        )


def offset_of(position):
    return TABLE_OFFSET + position * entries.ENTRY_SIZE


def placed(table):
    record = bytearray(RECORD_SIZE)

    for position, entry in enumerate(table):
        start = offset_of(position)
        record[start : start + entries.ENTRY_SIZE] = entry

    return record


def signed(record):
    struct.pack_into("<H", record, SIGNATURE_OFFSET, SIGNATURE)

    return bytes(record)


def build(table):
    refuse_more_than_the_table_holds(table)

    return signed(placed(table))


def entry_at(record, position):
    start = offset_of(position)

    return record[start : start + entries.ENTRY_SIZE]


def has_signature(record):
    return struct.unpack_from("<H", record, SIGNATURE_OFFSET)[0] == SIGNATURE