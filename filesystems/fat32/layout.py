from filesystems import regions
from filesystems.fat32 import bootsector

FIRST_DATA_CLUSTER = 2

BYTES_PER_SECTOR = "bytes_per_sector"
SECTORS_PER_CLUSTER = "sectors_per_cluster"
RESERVED_SECTORS = "reserved_sectors"
TABLES_PRESENT = "tables_present"
SECTORS_PER_TABLE = "sectors_per_table"
ROOT_CLUSTER = "root_cluster"
TOTAL_SECTORS = "total_sectors"


def parameters(region):
    return bootsector.read(regions.read(region, 0, bootsector.BYTES_PER_SECTOR))


def is_a_volume(parameters):
    return parameters["file_system"].startswith("FAT32") and parameters["signed"]


def refuse_when_not_a_volume(parameters):
    if not is_a_volume(parameters):
        raise ValueError("this region does not hold a FAT32 volume")


def bytes_per_cluster(parameters):
    return parameters[BYTES_PER_SECTOR] * parameters[SECTORS_PER_CLUSTER]


def first_table_sector(parameters):
    return parameters[RESERVED_SECTORS]


def table_sector(parameters, position):
    return first_table_sector(parameters) + position * parameters[SECTORS_PER_TABLE]


def first_data_sector(parameters):
    return first_table_sector(parameters) + (
        parameters[TABLES_PRESENT] * parameters[SECTORS_PER_TABLE]
    )


def sector_of_cluster(parameters, cluster):
    return first_data_sector(parameters) + (
        (cluster - FIRST_DATA_CLUSTER) * parameters[SECTORS_PER_CLUSTER]
    )


def data_clusters(parameters):
    available = parameters[TOTAL_SECTORS] - first_data_sector(parameters)

    return available // parameters[SECTORS_PER_CLUSTER]


def last_cluster(parameters):
    return FIRST_DATA_CLUSTER + data_clusters(parameters) - 1


def offset_of_sector(parameters, sector):
    return sector * parameters[BYTES_PER_SECTOR]


def offset_of_cluster(parameters, cluster):
    return offset_of_sector(parameters, sector_of_cluster(parameters, cluster))


def root_cluster(parameters):
    return parameters[ROOT_CLUSTER]


def is_within_data(parameters, cluster):
    return FIRST_DATA_CLUSTER <= cluster <= last_cluster(parameters)
