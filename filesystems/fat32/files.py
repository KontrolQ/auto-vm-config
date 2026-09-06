from filesystems.directories import entries
from filesystems.fat32 import allocation
from filesystems.fat32 import directories
from filesystems.fat32 import layout
from filesystems import regions

SEPARATORS = "/\\"

NO_FIRST_CLUSTER = 0
NOTHING_FOUND = None


def components_of(path):
    wanted = path

    for separator in SEPARATORS:
        wanted = wanted.replace(separator, SEPARATORS[0])

    return [component for component in wanted.split(SEPARATORS[0]) if component]


def parent_and_name(path):
    components = components_of(path)

    return components[:-1], components[-1]


def refuse_empty_path(path):
    if not components_of(path):
        raise ValueError("a file path is required")


def descended(region, parameters, cluster, component):
    found = directories.position_of(region, parameters, cluster, component)

    if found is NOTHING_FOUND:
        return NOTHING_FOUND

    held = directories.details_at(region, parameters, found[0], found[1])

    if not held["attributes"] & entries.DIRECTORY:
        return NOTHING_FOUND

    return held["first_cluster"]


def directory_cluster(region, parameters, components):
    cluster = layout.root_cluster(parameters)

    for component in components:
        cluster = descended(region, parameters, cluster, component)

        if cluster is NOTHING_FOUND:
            return NOTHING_FOUND

    return cluster


def made_directory(region, parameters, components, moment):
    cluster = layout.root_cluster(parameters)

    for component in components:
        descended_to = descended(region, parameters, cluster, component)

        if descended_to is NOTHING_FOUND:
            descended_to = directories.create(
                region, parameters, cluster, component, moment
            )

        cluster = descended_to

    return cluster


def clusters_needed(parameters, size):
    per_cluster = layout.bytes_per_cluster(parameters)

    return (size + per_cluster - 1) // per_cluster


def first_cluster_of(chain):
    if not chain:
        return NO_FIRST_CLUSTER

    return chain[0]


def piece_for(content, position, per_cluster):
    return content[position * per_cluster : (position + 1) * per_cluster]


def place_content(region, parameters, chain, content):
    per_cluster = layout.bytes_per_cluster(parameters)

    for position, cluster in enumerate(chain):
        piece = piece_for(content, position, per_cluster)

        regions.write(
            region,
            layout.offset_of_cluster(parameters, cluster),
            piece.ljust(per_cluster, b"\x00"),
        )


def read_content(region, parameters, chain, size):
    per_cluster = layout.bytes_per_cluster(parameters)
    gathered = b"".join(
        regions.read(region, layout.offset_of_cluster(parameters, cluster), per_cluster)
        for cluster in chain
    )

    return gathered[:size]


def refuse_when_missing(found, path):
    if found is NOTHING_FOUND:
        raise FileNotFoundError("%s is not on this volume" % path)


def located(region, parameters, path):
    components, name = parent_and_name(path)
    cluster = directory_cluster(region, parameters, components)

    if cluster is NOTHING_FOUND:
        return NOTHING_FOUND

    return directories.position_of(region, parameters, cluster, name)


def exists(region, parameters, path):
    return located(region, parameters, path) is not NOTHING_FOUND


def read(region, parameters, path):
    found = located(region, parameters, path)

    refuse_when_missing(found, path)

    held = directories.details_at(region, parameters, found[0], found[1])
    chain = allocation.chain_from(region, parameters, held["first_cluster"])

    return read_content(region, parameters, chain, held["size"])


def write(region, parameters, path, content, moment):
    refuse_empty_path(path)

    components, name = parent_and_name(path)
    parent = made_directory(region, parameters, components, moment)
    replacing = directories.position_of(region, parameters, parent, name)

    if replacing is not NOTHING_FOUND:
        held = directories.details_at(region, parameters, replacing[0], replacing[1])
        allocation.release(region, parameters, held["first_cluster"])

    chain = allocation.allocate(
        region, parameters, clusters_needed(parameters, len(content))
    )
    place_content(region, parameters, chain, content)

    raw = entries.build(
        name, entries.ARCHIVE, first_cluster_of(chain), len(content), moment
    )

    if replacing is not NOTHING_FOUND:
        directories.place(region, parameters, replacing[0], replacing[1], raw)

        return replacing

    return directories.add(region, parameters, parent, raw)


def remove(region, parameters, path):
    found = located(region, parameters, path)

    refuse_when_missing(found, path)

    held = directories.details_at(region, parameters, found[0], found[1])

    allocation.release(region, parameters, held["first_cluster"])
    directories.remove(region, parameters, found[0], found[1])


def listed(region, parameters, path=""):
    cluster = directory_cluster(region, parameters, components_of(path))

    refuse_when_missing(cluster, path)

    return directories.listed(region, parameters, cluster)


def free_space(region, parameters):
    return allocation.count_free(region, parameters) * layout.bytes_per_cluster(
        parameters
    )
