import struct

BYTES_PER_SECTOR = 512
BYTES_PER_ENTRY = 4

USABLE_BITS = 0x0FFFFFFF

FREE = 0x00000000
BAD = 0x0FFFFFF7
END_OF_CHAIN = 0x0FFFFFFF

MEDIA_DESCRIPTOR_ENTRY = 0x0FFFFFF8

FIRST_DATA_CLUSTER = 2

ENTRIES_PER_SECTOR = BYTES_PER_SECTOR // BYTES_PER_ENTRY


def masked(value):
    return value & USABLE_BITS


def sector_holding(cluster):
    return cluster // ENTRIES_PER_SECTOR


def offset_within_sector(cluster):
    return (cluster % ENTRIES_PER_SECTOR) * BYTES_PER_ENTRY


def entry_in(sector, cluster):
    return masked(struct.unpack_from("<I", sector, offset_within_sector(cluster))[0])


def place_entry(sector, cluster, value):
    struct.pack_into("<I", sector, offset_within_sector(cluster), masked(value))


def is_free(value):
    return masked(value) == FREE


def is_end_of_chain(value):
    return masked(value) >= BAD


def first_sector(occupied_clusters):
    sector = bytearray(BYTES_PER_SECTOR)

    place_entry(sector, 0, MEDIA_DESCRIPTOR_ENTRY)
    place_entry(sector, 1, END_OF_CHAIN)

    for position in range(occupied_clusters):
        place_entry(sector, FIRST_DATA_CLUSTER + position, END_OF_CHAIN)

    return bytes(sector)
