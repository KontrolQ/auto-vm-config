import sys

from disks import geometry
from filesystems.fat32 import formatting
from partitioning import entries
from partitioning import record

RUNNING_ON_WINDOWS = sys.platform == "win32"

SET_SPARSE = 0x000900C4


def allocate_only_what_is_written(handle):
    if not RUNNING_ON_WINDOWS:
        return

    import ctypes
    import msvcrt

    returned = ctypes.c_ulong(0)

    ctypes.windll.kernel32.DeviceIoControl(
        msvcrt.get_osfhandle(handle.fileno()),
        SET_SPARSE,
        None,
        0,
        None,
        0,
        ctypes.byref(returned),
        None,
    )


def reserve(handle, total_bytes):
    allocate_only_what_is_written(handle)
    handle.seek(total_bytes - 1)
    handle.write(b"\x00")


def place_sector(handle, sector, contents):
    handle.seek(geometry.offset_of_sector(sector))
    handle.write(contents)


def place_sectors(handle, base_sector, sectors):
    for relative_sector, contents in sectors:
        place_sector(handle, base_sector + relative_sector, contents)


def single_partition_record(partition_sectors, bootable):
    entry = entries.build(
        geometry.FIRST_PARTITION_SECTOR,
        partition_sectors,
        entries.TYPE_FAT32_LBA,
        bootable,
        geometry.SECTORS_PER_TRACK,
        geometry.HEADS_PER_CYLINDER,
    )

    return record.build([entry])


def create(path, total_bytes, volume_label, serial_number, moment, bootable):
    geometry.refuse_when_unaligned(total_bytes)

    total_sectors = geometry.sectors_in(total_bytes)
    partition_sectors = geometry.sectors_available_after_the_record(total_sectors)

    volume = formatting.sectors_for(
        partition_sectors,
        geometry.FIRST_PARTITION_SECTOR,
        geometry.SECTORS_PER_TRACK,
        geometry.HEADS_PER_CYLINDER,
        volume_label,
        serial_number,
        moment,
    )

    with open(path, "wb") as handle:
        reserve(handle, total_bytes)
        place_sector(handle, 0, single_partition_record(partition_sectors, bootable))
        place_sectors(handle, geometry.FIRST_PARTITION_SECTOR, volume)

    return {
        "path": path,
        "total_sectors": total_sectors,
        "partition_sectors": partition_sectors,
        "first_partition_sector": geometry.FIRST_PARTITION_SECTOR,
    }
