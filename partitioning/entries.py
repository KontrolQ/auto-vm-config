import struct

from partitioning import addressing

ENTRY_SIZE = 16

TYPE_FAT16 = 0x06
TYPE_FAT32 = 0x0B
TYPE_FAT32_LBA = 0x0C

STATUS_BOOTABLE = 0x80
STATUS_DORMANT = 0x00

STATUS_OFFSET = 0
FIRST_ADDRESS_OFFSET = 1
TYPE_OFFSET = 4
LAST_ADDRESS_OFFSET = 5
FIRST_SECTOR_OFFSET = 8
SECTOR_COUNT_OFFSET = 12


def status_for(bootable):
    return STATUS_BOOTABLE if bootable else STATUS_DORMANT


def build(
    first_sector,
    sector_count,
    partition_type,
    bootable,
    sectors_per_track,
    heads_per_cylinder,
):
    last_sector = first_sector + sector_count - 1

    return (
        bytes([status_for(bootable)])
        + addressing.packed_for(first_sector, sectors_per_track, heads_per_cylinder)
        + bytes([partition_type])
        + addressing.packed_for(last_sector, sectors_per_track, heads_per_cylinder)
        + struct.pack("<II", first_sector, sector_count)
    )


def read(raw):
    first_sector, sector_count = struct.unpack_from("<II", raw, FIRST_SECTOR_OFFSET)

    return {
        "bootable": raw[STATUS_OFFSET] == STATUS_BOOTABLE,
        "type": raw[TYPE_OFFSET],
        "first_sector": first_sector,
        "sectors": sector_count,
        "first_address": addressing.unpacked(
            raw[FIRST_ADDRESS_OFFSET : FIRST_ADDRESS_OFFSET + addressing.PACKED_SIZE]
        ),
        "last_address": addressing.unpacked(
            raw[LAST_ADDRESS_OFFSET : LAST_ADDRESS_OFFSET + addressing.PACKED_SIZE]
        ),
    }


def is_empty(raw):
    return raw[TYPE_OFFSET] == 0x00
