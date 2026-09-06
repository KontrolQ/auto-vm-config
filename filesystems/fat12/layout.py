import struct

from filesystems.directories import entries

BYTES_PER_SECTOR_OFFSET = 11
SECTORS_PER_CLUSTER_OFFSET = 13
RESERVED_SECTORS_OFFSET = 14
TABLES_PRESENT_OFFSET = 16
ROOT_ENTRIES_OFFSET = 17
SMALL_TOTAL_SECTORS_OFFSET = 19
MEDIA_DESCRIPTOR_OFFSET = 21
SECTORS_PER_TABLE_OFFSET = 22
SECTORS_PER_TRACK_OFFSET = 24
HEADS_PER_CYLINDER_OFFSET = 26
HIDDEN_SECTORS_OFFSET = 28
LARGE_TOTAL_SECTORS_OFFSET = 32

FIRST_DATA_CLUSTER = 2


def parameters(image):
    return {
        "bytes_per_sector": struct.unpack_from("<H", image, BYTES_PER_SECTOR_OFFSET)[0],
        "sectors_per_cluster": image[SECTORS_PER_CLUSTER_OFFSET],
        "reserved_sectors": struct.unpack_from("<H", image, RESERVED_SECTORS_OFFSET)[0],
        "tables_present": image[TABLES_PRESENT_OFFSET],
        "root_entries": struct.unpack_from("<H", image, ROOT_ENTRIES_OFFSET)[0],
        "small_total_sectors": struct.unpack_from("<H", image, SMALL_TOTAL_SECTORS_OFFSET)[0],
        "media_descriptor": image[MEDIA_DESCRIPTOR_OFFSET],
        "sectors_per_table": struct.unpack_from("<H", image, SECTORS_PER_TABLE_OFFSET)[0],
        "sectors_per_track": struct.unpack_from("<H", image, SECTORS_PER_TRACK_OFFSET)[0],
        "heads_per_cylinder": struct.unpack_from("<H", image, HEADS_PER_CYLINDER_OFFSET)[0],
        "hidden_sectors": struct.unpack_from("<I", image, HIDDEN_SECTORS_OFFSET)[0],
        "large_total_sectors": struct.unpack_from("<I", image, LARGE_TOTAL_SECTORS_OFFSET)[0],
    }


def total_sectors(parameters):
    return parameters["small_total_sectors"] or parameters["large_total_sectors"]


def bytes_per_cluster(parameters):
    return parameters["bytes_per_sector"] * parameters["sectors_per_cluster"]


def first_table_sector(parameters):
    return parameters["reserved_sectors"]


def root_sectors(parameters):
    occupied_bytes = parameters["root_entries"] * entries.ENTRY_SIZE

    return (occupied_bytes + parameters["bytes_per_sector"] - 1) // parameters["bytes_per_sector"]


def first_root_sector(parameters):
    return first_table_sector(parameters) + (
        parameters["tables_present"] * parameters["sectors_per_table"]
    )


def first_data_sector(parameters):
    return first_root_sector(parameters) + root_sectors(parameters)


def sector_of_cluster(parameters, cluster):
    return first_data_sector(parameters) + (
        (cluster - FIRST_DATA_CLUSTER) * parameters["sectors_per_cluster"]
    )


def data_clusters(parameters):
    available = total_sectors(parameters) - first_data_sector(parameters)

    return available // parameters["sectors_per_cluster"]


def offset_of_sector(parameters, sector):
    return sector * parameters["bytes_per_sector"]


def offset_of_cluster(parameters, cluster):
    return offset_of_sector(parameters, sector_of_cluster(parameters, cluster))
