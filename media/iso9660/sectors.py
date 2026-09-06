SECTOR_SIZE = 2048


def offset_of(logical_block):
    return logical_block * SECTOR_SIZE


def sectors_holding(length):
    return (length + SECTOR_SIZE - 1) // SECTOR_SIZE


def span(handle, logical_block, length):
    handle.seek(offset_of(logical_block))

    return handle.read(length)


def sector(handle, logical_block):
    return span(handle, logical_block, SECTOR_SIZE)
