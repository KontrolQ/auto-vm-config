import struct

from filesystems.fat12 import layout

USABLE_BITS = 0x0FFF

FREE = 0x000
BAD = 0xFF7
END_OF_CHAIN = 0xFFF

ODD_ENTRY_SHIFT = 4
LOW_NIBBLE = 0x000F
HIGH_NIBBLE = 0xF000


def holds_an_odd_entry(cluster):
    return cluster % 2 == 1


def offset_within_table(cluster):
    return (cluster * 3) // 2


def start_of_table(parameters, position):
    return layout.offset_of_sector(
        parameters,
        layout.first_table_sector(parameters) + position * parameters["sectors_per_table"],
    )


def offset_of(parameters, position, cluster):
    return start_of_table(parameters, position) + offset_within_table(cluster)


def unpacked(pair, cluster):
    if holds_an_odd_entry(cluster):
        return pair >> ODD_ENTRY_SHIFT

    return pair & USABLE_BITS


def repacked(pair, cluster, value):
    if holds_an_odd_entry(cluster):
        return (pair & LOW_NIBBLE) | ((value & USABLE_BITS) << ODD_ENTRY_SHIFT)

    return (pair & HIGH_NIBBLE) | (value & USABLE_BITS)


def entry(image, parameters, cluster):
    at = offset_of(parameters, 0, cluster)

    return unpacked(struct.unpack_from("<H", image, at)[0], cluster)


def place_entry(image, parameters, cluster, value):
    for position in range(parameters["tables_present"]):
        at = offset_of(parameters, position, cluster)
        pair = struct.unpack_from("<H", image, at)[0]

        struct.pack_into("<H", image, at, repacked(pair, cluster, value))


def is_free(value):
    return value == FREE


def is_end_of_chain(value):
    return value >= BAD


def chain_from(image, parameters, first_cluster):
    chain = []
    cluster = first_cluster

    while not is_end_of_chain(cluster) and cluster >= layout.FIRST_DATA_CLUSTER:
        chain.append(cluster)
        cluster = entry(image, parameters, cluster)

    return chain


def usable_clusters(parameters):
    return range(
        layout.FIRST_DATA_CLUSTER,
        layout.FIRST_DATA_CLUSTER + layout.data_clusters(parameters),
    )


def free_clusters(image, parameters):
    return [
        cluster
        for cluster in usable_clusters(parameters)
        if is_free(entry(image, parameters, cluster))
    ]


def linked(image, parameters, chain):
    for position, cluster in enumerate(chain[:-1]):
        place_entry(image, parameters, cluster, chain[position + 1])

    place_entry(image, parameters, chain[-1], END_OF_CHAIN)


def refuse_when_too_few_free(available, needed):
    if len(available) < needed:
        raise ValueError(
            "%d free clusters remain, %d are needed" % (len(available), needed)
        )


def allocate(image, parameters, needed):
    if needed == 0:
        return []

    available = free_clusters(image, parameters)

    refuse_when_too_few_free(available, needed)

    chain = available[:needed]
    linked(image, parameters, chain)

    return chain


def release(image, parameters, first_cluster):
    for cluster in chain_from(image, parameters, first_cluster):
        place_entry(image, parameters, cluster, FREE)
