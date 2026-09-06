from filesystems.directories import entries
from filesystems.fat12 import layout, root, table

NO_FIRST_CLUSTER = 0


def clusters_needed(parameters, size):
    per_cluster = layout.bytes_per_cluster(parameters)

    return (size + per_cluster - 1) // per_cluster


def first_cluster_of(chain):
    if not chain:
        return NO_FIRST_CLUSTER

    return chain[0]


def piece_for(content, position, per_cluster):
    return content[position * per_cluster : (position + 1) * per_cluster]


def place_cluster(image, parameters, cluster, piece):
    per_cluster = layout.bytes_per_cluster(parameters)
    at = layout.offset_of_cluster(parameters, cluster)

    image[at : at + per_cluster] = piece.ljust(per_cluster, b"\x00")


def read_cluster(image, parameters, cluster):
    per_cluster = layout.bytes_per_cluster(parameters)
    at = layout.offset_of_cluster(parameters, cluster)

    return bytes(image[at : at + per_cluster])


def place_content(image, parameters, chain, content):
    per_cluster = layout.bytes_per_cluster(parameters)

    for position, cluster in enumerate(chain):
        place_cluster(image, parameters, cluster, piece_for(content, position, per_cluster))


def read_content(image, parameters, chain, size):
    gathered = b"".join(read_cluster(image, parameters, cluster) for cluster in chain)

    return gathered[:size]


def refuse_when_missing(position, name):
    if position is None:
        raise FileNotFoundError(f"{name} is not in the root directory")


def details_at(image, parameters, position):
    return entries.read(root.slot(image, parameters, position))


def read(image, parameters, name):
    position = root.position_of(image, parameters, name)

    refuse_when_missing(position, name)

    details = details_at(image, parameters, position)
    chain = table.chain_from(image, parameters, details["first_cluster"])

    return read_content(image, parameters, chain, details["size"])


def exists(image, parameters, name):
    return root.position_of(image, parameters, name) is not None


def release_existing(image, parameters, position):
    table.release(image, parameters, details_at(image, parameters, position)["first_cluster"])


def write(image, parameters, name, content, moment):
    replacing = root.position_of(image, parameters, name)

    if replacing is not None:
        release_existing(image, parameters, replacing)

    chain = table.allocate(image, parameters, clusters_needed(parameters, len(content)))
    place_content(image, parameters, chain, content)

    raw = entries.build(name, entries.ARCHIVE, first_cluster_of(chain), len(content), moment)

    if replacing is not None:
        root.place(image, parameters, replacing, raw)
        return replacing

    return root.add(image, parameters, raw)


def remove(image, parameters, name):
    position = root.position_of(image, parameters, name)

    refuse_when_missing(position, name)
    release_existing(image, parameters, position)
    root.remove(image, parameters, position)


def free_space(image, parameters):
    return len(table.free_clusters(image, parameters)) * layout.bytes_per_cluster(parameters)
