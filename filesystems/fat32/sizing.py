BYTES_PER_SECTOR = 512

RESERVED_SECTORS = 32
TABLES_PRESENT = 2

SMALLEST_CLUSTER_COUNT = 65525
LARGEST_CLUSTER_COUNT = 268435444

BYTES_PER_TABLE_ENTRY = 4
CLUSTERS_RESERVED_AT_START = 2

CLUSTER_SIZE_BY_LARGEST_MEGABYTES = [
    (8192, 8),
    (16384, 16),
    (32768, 32),
]

LARGEST_SECTORS_PER_CLUSTER = 64


def megabytes_in(sector_count):
    return (sector_count * BYTES_PER_SECTOR) // (1024 * 1024)


def sectors_per_cluster_for(partition_sectors):
    partition_megabytes = megabytes_in(partition_sectors)

    for largest_megabytes, sectors_per_cluster in CLUSTER_SIZE_BY_LARGEST_MEGABYTES:
        if partition_megabytes <= largest_megabytes:
            return sectors_per_cluster

    return LARGEST_SECTORS_PER_CLUSTER


def sectors_for_entries(entry_count):
    needed_bytes = entry_count * BYTES_PER_TABLE_ENTRY

    return (needed_bytes + BYTES_PER_SECTOR - 1) // BYTES_PER_SECTOR


def clusters_available(partition_sectors, sectors_per_table, sectors_per_cluster):
    data_sectors = (
        partition_sectors - RESERVED_SECTORS - sectors_per_table * TABLES_PRESENT
    )

    return data_sectors // sectors_per_cluster


def table_size_for(partition_sectors, sectors_per_cluster):
    sectors_per_table = 1

    while True:
        cluster_count = clusters_available(
            partition_sectors, sectors_per_table, sectors_per_cluster
        )
        required = sectors_for_entries(cluster_count + CLUSTERS_RESERVED_AT_START)

        if required <= sectors_per_table:
            return sectors_per_table, cluster_count

        sectors_per_table = required


def is_large_enough(cluster_count):
    return cluster_count >= SMALLEST_CLUSTER_COUNT


def is_small_enough(cluster_count):
    return cluster_count <= LARGEST_CLUSTER_COUNT


def refuse_unusable_cluster_count(cluster_count):
    if not is_large_enough(cluster_count):
        raise ValueError(
            "%d clusters is fewer than the %d a FAT32 volume needs"
            % (cluster_count, SMALLEST_CLUSTER_COUNT)
        )

    if not is_small_enough(cluster_count):
        raise ValueError(
            "%d clusters is more than the %d a FAT32 volume holds"
            % (cluster_count, LARGEST_CLUSTER_COUNT)
        )


def plan_for(partition_sectors):
    sectors_per_cluster = sectors_per_cluster_for(partition_sectors)
    sectors_per_table, cluster_count = table_size_for(
        partition_sectors, sectors_per_cluster
    )

    refuse_unusable_cluster_count(cluster_count)

    return {
        "partition_sectors": partition_sectors,
        "sectors_per_cluster": sectors_per_cluster,
        "sectors_per_table": sectors_per_table,
        "clusters": cluster_count,
    }