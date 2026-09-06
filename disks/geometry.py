BYTES_PER_SECTOR = 512

SECTORS_PER_TRACK = 63
HEADS_PER_CYLINDER = 255

FIRST_PARTITION_SECTOR = SECTORS_PER_TRACK


def sectors_in(total_bytes):
    return total_bytes // BYTES_PER_SECTOR


def bytes_in(sector_count):
    return sector_count * BYTES_PER_SECTOR


def offset_of_sector(sector):
    return bytes_in(sector)


def sectors_available_after_the_record(total_sectors):
    return total_sectors - FIRST_PARTITION_SECTOR


def refuse_when_unaligned(total_bytes):
    if total_bytes % BYTES_PER_SECTOR:
        raise ValueError(
            f"{total_bytes} bytes is not a whole number of {BYTES_PER_SECTOR} byte sectors"
        )
