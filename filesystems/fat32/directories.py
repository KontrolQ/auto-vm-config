from filesystems.directories import entries
from filesystems.fat32 import allocation
from filesystems.fat32 import layout
from filesystems import regions

ROOT_PARENT_CLUSTER = 0

NO_SIZE = 0
NOTHING_FOUND = None


def slots_per_cluster(parameters):
    return layout.bytes_per_cluster(parameters) // entries.ENTRY_SIZE


def slot_offset(parameters, cluster, index):
    return layout.offset_of_cluster(parameters, cluster) + index * entries.ENTRY_SIZE


def slot(region, parameters, cluster, index):
    return regions.read(
        region, slot_offset(parameters, cluster, index), entries.ENTRY_SIZE
    )


def place(region, parameters, cluster, index, raw):
    regions.write(region, slot_offset(parameters, cluster, index), raw)


def positions_in(region, parameters, first_cluster):
    found = []

    for cluster in allocation.chain_from(region, parameters, first_cluster):
        for index in range(slots_per_cluster(parameters)):
            raw = slot(region, parameters, cluster, index)

            if entries.ends_the_directory(raw):
                return found

            if entries.holds_a_file(raw):
                found.append((cluster, index))

    return found


def listed(region, parameters, first_cluster):
    return [
        entries.read(slot(region, parameters, cluster, index))
        for cluster, index in positions_in(region, parameters, first_cluster)
    ]


def names(region, parameters, first_cluster):
    return [held["name"] for held in listed(region, parameters, first_cluster)]


def matches(raw, name):
    return entries.read(raw)["name"].upper() == name.upper()


def position_of(region, parameters, first_cluster, name):
    for cluster, index in positions_in(region, parameters, first_cluster):
        if matches(slot(region, parameters, cluster, index), name):
            return cluster, index

    return NOTHING_FOUND


def details_at(region, parameters, cluster, index):
    return entries.read(slot(region, parameters, cluster, index))


def is_available(raw):
    return entries.ends_the_directory(raw) or entries.is_deleted(raw)


def first_available(region, parameters, first_cluster):
    for cluster in allocation.chain_from(region, parameters, first_cluster):
        for index in range(slots_per_cluster(parameters)):
            if is_available(slot(region, parameters, cluster, index)):
                return cluster, index

    return NOTHING_FOUND


def emptied(region, parameters, cluster):
    regions.fill(
        region, layout.offset_of_cluster(parameters, cluster),
        layout.bytes_per_cluster(parameters),
    )


def grown(region, parameters, first_cluster):
    chain = allocation.chain_from(region, parameters, first_cluster)
    added = allocation.extend(region, parameters, chain[-1], 1)

    emptied(region, parameters, added[0])

    return added[0], 0


def add(region, parameters, first_cluster, raw):
    found = first_available(region, parameters, first_cluster)

    if found is NOTHING_FOUND:
        found = grown(region, parameters, first_cluster)

    place(region, parameters, found[0], found[1], raw)

    return found


def remove(region, parameters, cluster, index):
    raw = bytearray(slot(region, parameters, cluster, index))
    raw[0] = entries.DELETED

    place(region, parameters, cluster, index, bytes(raw))


def parent_reference(parent_cluster, parameters):
    if parent_cluster == layout.root_cluster(parameters):
        return ROOT_PARENT_CLUSTER

    return parent_cluster


def marked_as_directory(region, parameters, cluster, parent_cluster, moment):
    emptied(region, parameters, cluster)

    place(
        region, parameters, cluster, 0,
        entries.with_raw_name(
            entries.SELF_NAME, entries.DIRECTORY, cluster, NO_SIZE, moment
        ),
    )
    place(
        region, parameters, cluster, 1,
        entries.with_raw_name(
            entries.PARENT_NAME,
            entries.DIRECTORY,
            parent_reference(parent_cluster, parameters),
            NO_SIZE,
            moment,
        ),
    )


def create(region, parameters, parent_cluster, name, moment):
    cluster = allocation.allocate(region, parameters, 1)[0]

    marked_as_directory(region, parameters, cluster, parent_cluster, moment)
    add(
        region, parameters, parent_cluster,
        entries.build(name, entries.DIRECTORY, cluster, NO_SIZE, moment),
    )

    return cluster
