import struct

from filesystems.fat32 import bootsector
from filesystems.fat32 import information
from filesystems.fat32 import layout
from filesystems.fat32 import table
from filesystems import regions

BYTES_PER_ENTRY = 4

RESERVED_BITS = 0xF0000000

CHUNK_SECTORS = 64

NO_CLUSTER = 0


def entry_offset(parameters, position, cluster):
    return (
        layout.offset_of_sector(parameters, layout.table_sector(parameters, position))
        + cluster * BYTES_PER_ENTRY
    )


def entry(region, parameters, cluster):
    raw = regions.read(region, entry_offset(parameters, 0, cluster), BYTES_PER_ENTRY)

    return table.masked(struct.unpack("<I", raw)[0])


def place_entry(region, parameters, cluster, value):
    for position in range(parameters[layout.TABLES_PRESENT]):
        at = entry_offset(parameters, position, cluster)
        existing = struct.unpack("<I", regions.read(region, at, BYTES_PER_ENTRY))[0]
        merged = (existing & RESERVED_BITS) | table.masked(value)

        regions.write(region, at, struct.pack("<I", merged))


def chain_from(region, parameters, first_cluster):
    chain = []
    cluster = first_cluster

    while layout.is_within_data(parameters, cluster):
        chain.append(cluster)
        cluster = entry(region, parameters, cluster)

    return chain


def entries_in(raw):
    count = len(raw) // BYTES_PER_ENTRY

    return struct.unpack("<%dI" % count, raw[: count * BYTES_PER_ENTRY])


def clusters_per_chunk(parameters):
    return (parameters[layout.BYTES_PER_SECTOR] // BYTES_PER_ENTRY) * CHUNK_SECTORS


def gather_free_between(region, parameters, first, final, needed, found):
    base = layout.offset_of_sector(parameters, layout.table_sector(parameters, 0))
    stride = clusters_per_chunk(parameters)
    cluster = first

    while cluster <= final and len(found) < needed:
        wanted = min(stride, final - cluster + 1)
        raw = regions.read(
            region, base + cluster * BYTES_PER_ENTRY, wanted * BYTES_PER_ENTRY
        )

        for position, value in enumerate(entries_in(raw)):
            if table.masked(value) == table.FREE:
                found.append(cluster + position)

                if len(found) >= needed:
                    return found

        cluster += wanted

    return found


def free_clusters(region, parameters, needed, hint):
    first = layout.FIRST_DATA_CLUSTER
    final = layout.last_cluster(parameters)
    begin = min(max(hint, first), final)

    found = gather_free_between(region, parameters, begin, final, needed, [])

    if len(found) < needed:
        found = gather_free_between(
            region, parameters, first, begin - 1, needed, found
        )

    return found


def count_free(region, parameters):
    return len(
        gather_free_between(
            region,
            parameters,
            layout.FIRST_DATA_CLUSTER,
            layout.last_cluster(parameters),
            layout.data_clusters(parameters),
            [],
        )
    )


def information_offset(parameters):
    return layout.offset_of_sector(parameters, bootsector.INFORMATION_SECTOR)


def read_information(region, parameters):
    return information.read(
        regions.read(region, information_offset(parameters), information.BYTES_PER_SECTOR)
    )


def write_information(region, parameters, free_count, next_free):
    regions.write(
        region, information_offset(parameters), information.build(free_count, next_free)
    )


def allocation_hint(region, parameters):
    held = read_information(region, parameters)["next_free_cluster"]

    if layout.is_within_data(parameters, held):
        return held

    return layout.FIRST_DATA_CLUSTER


def refuse_when_too_few_free(found, needed):
    if len(found) < needed:
        raise ValueError(
            "%d free clusters remain, %d are needed" % (len(found), needed)
        )


def linked(region, parameters, chain):
    for position, cluster in enumerate(chain[:-1]):
        place_entry(region, parameters, cluster, chain[position + 1])

    place_entry(region, parameters, chain[-1], table.END_OF_CHAIN)


def note_allocation(region, parameters, chain):
    held = read_information(region, parameters)
    free_count = held["free_clusters"]

    if free_count == information.UNKNOWN:
        free_count = count_free(region, parameters)
    else:
        free_count -= len(chain)

    write_information(region, parameters, free_count, chain[-1] + 1)


def allocate(region, parameters, needed):
    if needed == 0:
        return []

    found = free_clusters(
        region, parameters, needed, allocation_hint(region, parameters)
    )

    refuse_when_too_few_free(found, needed)
    linked(region, parameters, found)
    note_allocation(region, parameters, found)

    return found


def extend(region, parameters, last_cluster, needed):
    added = allocate(region, parameters, needed)

    if added:
        place_entry(region, parameters, last_cluster, added[0])

    return added


def release(region, parameters, first_cluster):
    chain = chain_from(region, parameters, first_cluster)

    for cluster in chain:
        place_entry(region, parameters, cluster, table.FREE)

    if chain:
        held = read_information(region, parameters)
        write_information(
            region, parameters, held["free_clusters"] + len(chain), chain[0]
        )

    return chain
