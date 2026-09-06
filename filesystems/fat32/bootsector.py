import struct

from filesystems.naming import labels

BYTES_PER_SECTOR = 512

JUMP_INSTRUCTION = b"\xeb\x58\x90"
CREATOR_NAME = b"MSWIN4.1"
FILE_SYSTEM_NAME = b"FAT32   "

MEDIA_DESCRIPTOR_FIXED_DISK = 0xF8

ROOT_CLUSTER = 2
INFORMATION_SECTOR = 1
BACKUP_SECTOR = 6

DRIVE_NUMBER_FIRST_FIXED_DISK = 0x80
EXTENDED_SIGNATURE = 0x29

LABEL_OFFSET = 71

SIGNATURE_OFFSET = 510
SIGNATURE = 0xAA55


def build(
    partition_sectors,
    sectors_per_cluster,
    sectors_per_table,
    first_partition_sector,
    sectors_per_track,
    heads_per_cylinder,
    volume_label,
    serial_number,
    tables_present,
    reserved_sectors,
):
    sector = bytearray(BYTES_PER_SECTOR)

    sector[0:3] = JUMP_INSTRUCTION
    sector[3:11] = CREATOR_NAME

    struct.pack_into("<H", sector, 11, BYTES_PER_SECTOR)
    sector[13] = sectors_per_cluster
    struct.pack_into("<H", sector, 14, reserved_sectors)
    sector[16] = tables_present
    struct.pack_into("<H", sector, 17, 0)
    struct.pack_into("<H", sector, 19, 0)
    sector[21] = MEDIA_DESCRIPTOR_FIXED_DISK
    struct.pack_into("<H", sector, 22, 0)
    struct.pack_into("<H", sector, 24, sectors_per_track)
    struct.pack_into("<H", sector, 26, heads_per_cylinder)
    struct.pack_into("<I", sector, 28, first_partition_sector)
    struct.pack_into("<I", sector, 32, partition_sectors)

    struct.pack_into("<I", sector, 36, sectors_per_table)
    struct.pack_into("<H", sector, 40, 0)
    struct.pack_into("<H", sector, 42, 0)
    struct.pack_into("<I", sector, 44, ROOT_CLUSTER)
    struct.pack_into("<H", sector, 48, INFORMATION_SECTOR)
    struct.pack_into("<H", sector, 50, BACKUP_SECTOR)

    sector[64] = DRIVE_NUMBER_FIRST_FIXED_DISK
    sector[66] = EXTENDED_SIGNATURE
    struct.pack_into("<I", sector, 67, serial_number)
    sector[LABEL_OFFSET : LABEL_OFFSET + labels.LENGTH] = labels.encoded(volume_label)
    sector[82:90] = FILE_SYSTEM_NAME

    struct.pack_into("<H", sector, SIGNATURE_OFFSET, SIGNATURE)

    return bytes(sector)


def read(sector):
    return {
        "creator": sector[3:11].decode("ascii", "replace"),
        "bytes_per_sector": struct.unpack_from("<H", sector, 11)[0],
        "sectors_per_cluster": sector[13],
        "reserved_sectors": struct.unpack_from("<H", sector, 14)[0],
        "tables_present": sector[16],
        "sectors_per_table": struct.unpack_from("<I", sector, 36)[0],
        "root_cluster": struct.unpack_from("<I", sector, 44)[0],
        "total_sectors": struct.unpack_from("<I", sector, 32)[0],
        "volume_label": labels.decoded(sector[LABEL_OFFSET:]),
        "file_system": sector[82:90].decode("ascii", "replace").strip(),
        "signed": struct.unpack_from("<H", sector, SIGNATURE_OFFSET)[0] == SIGNATURE,
    }