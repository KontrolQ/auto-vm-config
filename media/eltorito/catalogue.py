import struct

ENTRY_SIZE = 32

VALIDATION_ENTRY_OFFSET = 0
INITIAL_ENTRY_OFFSET = 32

HEADER_IDENTIFIER = 1
HEADER_OFFSET = 0

KEY_OFFSET = 30
KEY = 0xAA55

CHECKSUM_WORDS = ENTRY_SIZE // 2
CHECKSUM_MODULUS = 0x10000

PLATFORM_OFFSET = 1
PLATFORM_X86 = 0x00
PLATFORM_POWERPC = 0x01
PLATFORM_MACINTOSH = 0x02
PLATFORM_EFI = 0xEF

BOOTABLE_OFFSET = 0
BOOTABLE = 0x88
NOT_BOOTABLE = 0x00

MEDIA_TYPE_OFFSET = 1
NO_EMULATION = 0x00
FLOPPY_1200 = 0x01
FLOPPY_1440 = 0x02
FLOPPY_2880 = 0x03
HARD_DISK = 0x04

MEDIA_TYPE_MASK = 0x0F

LOAD_SEGMENT_OFFSET = 2
SYSTEM_TYPE_OFFSET = 4
SECTOR_COUNT_OFFSET = 6
LOAD_BLOCK_OFFSET = 8

VIRTUAL_SECTOR_SIZE = 512

FLOPPY_SIZES = {
    FLOPPY_1200: 1228800,
    FLOPPY_1440: 1474560,
    FLOPPY_2880: 2949120,
}

MEDIA_NAMES = {
    NO_EMULATION: "no emulation",
    FLOPPY_1200: "1.2 MB floppy",
    FLOPPY_1440: "1.44 MB floppy",
    FLOPPY_2880: "2.88 MB floppy",
    HARD_DISK: "hard disk",
}


def validation_entry(raw):
    return raw[VALIDATION_ENTRY_OFFSET : VALIDATION_ENTRY_OFFSET + ENTRY_SIZE]


def initial_entry(raw):
    return raw[INITIAL_ENTRY_OFFSET : INITIAL_ENTRY_OFFSET + ENTRY_SIZE]


def checksum_of(entry):
    words = struct.unpack_from("<%dH" % CHECKSUM_WORDS, entry, 0)

    return sum(words) % CHECKSUM_MODULUS


def has_header(entry):
    return entry[HEADER_OFFSET] == HEADER_IDENTIFIER


def has_key(entry):
    return struct.unpack_from("<H", entry, KEY_OFFSET)[0] == KEY


def is_valid(raw):
    entry = validation_entry(raw)

    return has_header(entry) and has_key(entry) and checksum_of(entry) == 0


def platform_of(raw):
    return validation_entry(raw)[PLATFORM_OFFSET]


def is_bootable(entry):
    return entry[BOOTABLE_OFFSET] == BOOTABLE


def media_type_of(entry):
    return entry[MEDIA_TYPE_OFFSET] & MEDIA_TYPE_MASK


def media_name_of(entry):
    return MEDIA_NAMES.get(media_type_of(entry), "unknown")


def is_a_floppy(entry):
    return media_type_of(entry) in FLOPPY_SIZES


def sector_count_of(entry):
    return struct.unpack_from("<H", entry, SECTOR_COUNT_OFFSET)[0]


def load_block_of(entry):
    return struct.unpack_from("<I", entry, LOAD_BLOCK_OFFSET)[0]


def size_of(entry):
    emulated = FLOPPY_SIZES.get(media_type_of(entry))

    if emulated is not None:
        return emulated

    return sector_count_of(entry) * VIRTUAL_SECTOR_SIZE


def read(raw):
    entry = initial_entry(raw)

    return {
        "bootable": is_bootable(entry),
        "media_type": media_type_of(entry),
        "media": media_name_of(entry),
        "floppy": is_a_floppy(entry),
        "load_block": load_block_of(entry),
        "sectors": sector_count_of(entry),
        "size": size_of(entry),
    }
