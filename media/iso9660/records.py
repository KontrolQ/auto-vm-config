import struct

LENGTH_OFFSET = 0
EXTENT_OFFSET = 2
DATA_LENGTH_OFFSET = 10
FLAGS_OFFSET = 25
IDENTIFIER_LENGTH_OFFSET = 32
IDENTIFIER_OFFSET = 33

HIDDEN_FLAG = 0x01
DIRECTORY_FLAG = 0x02

VERSION_SEPARATOR = ";"

CURRENT_DIRECTORY_IDENTIFIER = b"\x00"
PARENT_DIRECTORY_IDENTIFIER = b"\x01"


def length_of(raw, at):
    return raw[at]


def sized(raw, at):
    return raw[at : at + length_of(raw, at)]


def extent_of(record):
    return struct.unpack_from("<I", record, EXTENT_OFFSET)[0]


def data_length_of(record):
    return struct.unpack_from("<I", record, DATA_LENGTH_OFFSET)[0]


def flags_of(record):
    return record[FLAGS_OFFSET]


def is_directory(record):
    return bool(flags_of(record) & DIRECTORY_FLAG)


def is_hidden(record):
    return bool(flags_of(record) & HIDDEN_FLAG)


def identifier_of(record):
    length = record[IDENTIFIER_LENGTH_OFFSET]

    return record[IDENTIFIER_OFFSET : IDENTIFIER_OFFSET + length]


def is_current_directory(record):
    return identifier_of(record) == CURRENT_DIRECTORY_IDENTIFIER


def is_parent_directory(record):
    return identifier_of(record) == PARENT_DIRECTORY_IDENTIFIER


def is_special(record):
    return is_current_directory(record) or is_parent_directory(record)


def without_version(identifier):
    return identifier.split(VERSION_SEPARATOR)[0]


def name_of(record):
    return without_version(identifier_of(record).decode("ascii", "replace"))


def read(record):
    return {
        "name": name_of(record),
        "extent": extent_of(record),
        "size": data_length_of(record),
        "directory": is_directory(record),
    }
