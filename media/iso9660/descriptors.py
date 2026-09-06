import struct

from media.iso9660 import sectors

STANDARD_IDENTIFIER = b"CD001"

TYPE_OFFSET = 0
IDENTIFIER_OFFSET = 1
IDENTIFIER_LENGTH = 5

BOOT_RECORD = 0
PRIMARY = 1
SUPPLEMENTARY = 2
TERMINATOR = 255

FIRST_SECTOR = 16
MOST_EXPECTED = 64

VOLUME_IDENTIFIER_OFFSET = 40
VOLUME_IDENTIFIER_LENGTH = 32

VOLUME_SPACE_SIZE_OFFSET = 80
LOGICAL_BLOCK_SIZE_OFFSET = 128

ROOT_RECORD_OFFSET = 156
ROOT_RECORD_LENGTH = 34

PUBLISHER_OFFSET = 318
PUBLISHER_LENGTH = 128

BOOT_SYSTEM_IDENTIFIER_OFFSET = 7
BOOT_SYSTEM_IDENTIFIER_LENGTH = 32
BOOT_CATALOGUE_OFFSET = 71


def is_a_descriptor(raw):
    return (
        len(raw) >= sectors.SECTOR_SIZE
        and raw[IDENTIFIER_OFFSET : IDENTIFIER_OFFSET + IDENTIFIER_LENGTH] == STANDARD_IDENTIFIER
    )


def type_of(raw):
    return raw[TYPE_OFFSET]


def text_at(raw, offset, length):
    return raw[offset : offset + length].decode("ascii", "replace").strip()


def all_of(handle):
    found = []
    logical_block = FIRST_SECTOR

    while len(found) < MOST_EXPECTED:
        raw = sectors.sector(handle, logical_block)

        if not is_a_descriptor(raw):
            return found

        found.append(raw)

        if type_of(raw) == TERMINATOR:
            return found

        logical_block += 1

    return found


def of_type(handle, wanted):
    for raw in all_of(handle):
        if type_of(raw) == wanted:
            return raw

    return None


def primary(handle):
    return of_type(handle, PRIMARY)


def boot_record(handle):
    return of_type(handle, BOOT_RECORD)


def holds_a_volume(handle):
    return primary(handle) is not None


def volume_identifier(raw):
    return text_at(raw, VOLUME_IDENTIFIER_OFFSET, VOLUME_IDENTIFIER_LENGTH)


def publisher(raw):
    return text_at(raw, PUBLISHER_OFFSET, PUBLISHER_LENGTH)


def volume_sectors(raw):
    return struct.unpack_from("<I", raw, VOLUME_SPACE_SIZE_OFFSET)[0]


def logical_block_size(raw):
    return struct.unpack_from("<H", raw, LOGICAL_BLOCK_SIZE_OFFSET)[0]


def root_record(raw):
    return raw[ROOT_RECORD_OFFSET : ROOT_RECORD_OFFSET + ROOT_RECORD_LENGTH]


def boot_system_identifier(raw):
    return text_at(raw, BOOT_SYSTEM_IDENTIFIER_OFFSET, BOOT_SYSTEM_IDENTIFIER_LENGTH)


def boot_catalogue_block(raw):
    return struct.unpack_from("<I", raw, BOOT_CATALOGUE_OFFSET)[0]
