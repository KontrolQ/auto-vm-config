import struct

BYTES_PER_SECTOR = 512

LEADING_SIGNATURE = 0x41615252
STRUCTURE_SIGNATURE = 0x61417272
TRAILING_SIGNATURE = 0xAA550000

LEADING_OFFSET = 0
STRUCTURE_OFFSET = 484
FREE_COUNT_OFFSET = 488
NEXT_FREE_OFFSET = 492
TRAILING_OFFSET = 508

UNKNOWN = 0xFFFFFFFF


def build(free_clusters, next_free_cluster):
    sector = bytearray(BYTES_PER_SECTOR)

    struct.pack_into("<I", sector, LEADING_OFFSET, LEADING_SIGNATURE)
    struct.pack_into("<I", sector, STRUCTURE_OFFSET, STRUCTURE_SIGNATURE)
    struct.pack_into("<I", sector, FREE_COUNT_OFFSET, free_clusters)
    struct.pack_into("<I", sector, NEXT_FREE_OFFSET, next_free_cluster)
    struct.pack_into("<I", sector, TRAILING_OFFSET, TRAILING_SIGNATURE)

    return bytes(sector)


def read(sector):
    return {
        "free_clusters": struct.unpack_from("<I", sector, FREE_COUNT_OFFSET)[0],
        "next_free_cluster": struct.unpack_from("<I", sector, NEXT_FREE_OFFSET)[0],
        "signed": struct.unpack_from("<I", sector, LEADING_OFFSET)[0] == LEADING_SIGNATURE
        and struct.unpack_from("<I", sector, STRUCTURE_OFFSET)[0] == STRUCTURE_SIGNATURE
        and struct.unpack_from("<I", sector, TRAILING_OFFSET)[0] == TRAILING_SIGNATURE,
    }
