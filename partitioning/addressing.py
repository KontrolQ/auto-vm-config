LARGEST_ADDRESSABLE_CYLINDER = 1023
PACKED_SIZE = 3


def address_of(absolute_sector, sectors_per_track, heads_per_cylinder):
    sectors_per_cylinder = heads_per_cylinder * sectors_per_track
    remainder = absolute_sector % sectors_per_cylinder

    return (
        absolute_sector // sectors_per_cylinder,
        remainder // sectors_per_track,
        (remainder % sectors_per_track) + 1,
    )


def is_addressable(address):
    return address[0] <= LARGEST_ADDRESSABLE_CYLINDER


def furthest_address(sectors_per_track, heads_per_cylinder):
    return LARGEST_ADDRESSABLE_CYLINDER, heads_per_cylinder - 1, sectors_per_track


def clamped(address, sectors_per_track, heads_per_cylinder):
    if is_addressable(address):
        return address

    return furthest_address(sectors_per_track, heads_per_cylinder)


def packed(address):
    cylinder, head, sector = address

    return bytes([head, ((cylinder >> 2) & 0xC0) | sector, cylinder & 0xFF])


def unpacked(raw):
    return ((raw[1] & 0xC0) << 2) | raw[2], raw[0], raw[1] & 0x3F


def packed_for(absolute_sector, sectors_per_track, heads_per_cylinder):
    address = address_of(absolute_sector, sectors_per_track, heads_per_cylinder)

    return packed(clamped(address, sectors_per_track, heads_per_cylinder))
